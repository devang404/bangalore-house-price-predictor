from flask import Flask, request, jsonify, render_template, session
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

import numpy as np
import pickle
import json
import pandas as pd
from flask_cors import CORS
import requests
import sqlite3
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key_123')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
login_manager.login_message_category = "info"
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"
CORS(app)

# Location tiers removed (handled by model)

# Load the trained model
import os
import json
import pickle

model_file = "banglore_home_prices_model.pickle"
columns_file = "columns.json"

try:
    # Check if model and column files exist
    if not os.path.exists(model_file):
        raise FileNotFoundError(f"❌ Model file '{model_file}' not found.")
    
    if not os.path.exists(columns_file):
        raise FileNotFoundError(f"❌ Columns file '{columns_file}' not found.")

    # Load the model
    with open(model_file, "rb") as f:
        model = pickle.load(f)
    
    # Load column names
    with open(columns_file, "r") as f:
        data_columns = json.load(f)["data_columns"]

    if len(data_columns) < 4:
        raise ValueError("❌ Invalid data_columns format. Expected at least 4 columns (sqft, bath, bhk, property_age, locations).")

    # Extract locations (assuming first 3 columns are fixed: sqft, bath, bhk)
    locations = data_columns[3:]

    print(f"✅ Model and {len(locations)} locations loaded successfully!")

except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None
    data_columns = []
    locations = []




# --- Define simple models used by the app ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# Flask-Login user loader: required so `current_user` can be resolved in templates
@login_manager.user_loader
def load_user(user_id):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    sqft = db.Column(db.Float, nullable=False)
    bhk = db.Column(db.Integer, nullable=False)
    bath = db.Column(db.Integer, nullable=False)
    property_age = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))




def calculate_age_factor(age: int) -> float:
    """Calculate depreciation multiplier based on property age.
    Up to 40% reduction for 20-year-old properties.
    """
    try:
        age = int(age)
    except Exception:
        age = 0
    return 1 - (min(max(age, 0), 20) / 20) * 0.4


@app.route("/predict_price", methods=["POST"])
def predict_price():
    try:
        data = request.get_json() or {}
        print("📥 Received Data for Prediction:", data)

        if model is None or not data_columns:
            return jsonify({"error": "Model or data columns not loaded."}), 500

        # Build feature vector
        features = np.zeros(len(data_columns))

        # Numeric fields
        try:
            if "total_sqft" in data_columns:
                features[data_columns.index("total_sqft")] = float(data.get("total_sqft", 0) or 0)
            if "bath" in data_columns:
                features[data_columns.index("bath")] = int(data.get("bath", 0) or 0)
            if "property_age" in data_columns:
                features[data_columns.index("property_age")] = int(data.get("property_age", 0) or 0)
            if "bhk" in data_columns:
                features[data_columns.index("bhk")] = int(data.get("bhk", 0) or 0)
        except Exception as e:
            print(f"⚠️ Numeric conversion error: {e}")
            return jsonify({"error": "Invalid numeric input."}), 400

        # Location one-hot
        location = (data.get("location") or "").strip()
        location_found = False
        if location:
            for idx, col in enumerate(data_columns):
                if col.lower() == location.lower():
                    features[idx] = 1
                    location_found = True
                    break

        # If model isn't loaded, use a simple heuristic for base_price so endpoint remains testable
        if model is None:
            try:
                sqft = float(data.get("total_sqft", 0) or 0)
            except Exception:
                sqft = 0
            bhk = int(data.get("bhk", 0) or 0)
            # Simple heuristic: base price in currency units (e.g., Rupees) ~ sqft * rate + bhk premium
            base_price = sqft * 3000 + bhk * 200000
        else:
            # Predict base price with patch for sklearn compatibility if needed
            try:
                base_price = model.predict([features])[0]
            except AttributeError as e:
                # Compatibility hack for older sklearn-saved ensembles
                if 'monotonic_cst' in str(e):
                    def _patch_estimator(est):
                        if not hasattr(est, 'monotonic_cst'):
                            setattr(est, 'monotonic_cst', None)
                        if hasattr(est, 'estimators_'):
                            for sub in getattr(est, 'estimators_'):
                                _patch_estimator(sub)
                    _patch_estimator(model)
                    base_price = model.predict([features])[0]
                else:
                    return jsonify({"error": str(e)}), 500

        # Apply age depreciation (Model trained on new raw data, so we depreciate for age manually)
        age = int(data.get("property_age", 0) or 0)
        age_factor = calculate_age_factor(age)

        # Final price calculation (Base Price * Age Factor)
        # We removed manual location multipliers because the model now natively understands location value via one-hot encoding.
        final_price = base_price * age_factor

        print(f"💰 Base Price: {base_price:.2f}")
        print(f"🏗️ Age Factor: {age_factor:.2f} (Depreciation for {age} years)")
        print(f"💵 Final Price: {final_price:.2f}")

        return jsonify({
            "estimated_price": round(float(final_price), 2),
            "details": {
                "base_price": round(float(base_price), 2),
                "age_factor": round(age_factor, 2)
            }
        })

    except Exception as e:
        print(f"❌ Error in Prediction: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/")
def index():
    """Serve main application page."""
    return render_template('app.html')


@app.route('/login_page')
def login_page():
    """Serve login page."""
    return render_template('login.html')


@app.route('/register_page')
def register_page():
    """Serve registration page."""
    return render_template('register.html')


def get_location_from_db(location_name):
    """Fetch coordinates from SQLite database."""
    conn = sqlite3.connect("house_prices.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT latitude, longitude FROM heatmap_data WHERE TRIM(LOWER(location)) = LOWER(?)", (location_name.strip(),))
    result = cursor.fetchone()
    
    conn.close()
    return result if result else None

def fetch_from_osm(location_name):
    """Fetches coordinates from OpenStreetMap API if not found in database."""
    try:
        response = requests.get(NOMINATIM_API_URL, params={"q": location_name, "format": "json"}, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data:
            lat, lon = float(data[0]["lat"]), float(data[0]["lon"])
            return lat, lon
    except Exception as e:
        print(f"🌍 OSM Fetch Error: {e}")
    return None

def save_location_to_db(location_name, lat, lon):
    """Saves a new location to the database for future use."""
    conn = sqlite3.connect("house_prices.db")
    cursor = conn.cursor()
    try:
        cursor.execute("CREATE TABLE IF NOT EXISTS heatmap_data (id INTEGER PRIMARY KEY AUTOINCREMENT, location TEXT, latitude REAL, longitude REAL)")
        cursor.execute("INSERT INTO heatmap_data (location, latitude, longitude) VALUES (?, ?, ?)", (location_name.strip(), lat, lon))
        conn.commit()
        print(f"✅ Saved {location_name} to database!")
    except Exception as e:
        print(f"❌ Failed to save location to DB: {e}")
    finally:
        conn.close()
@app.route("/get_location_coords", methods=["GET"])
def get_location_coords():
    location = request.args.get("location", "").strip()

    if not location:
        return jsonify({"error": "Location not provided"}), 400

    # First, check database
    coords = get_location_from_db(location)
    if coords:
        return jsonify({"lat": coords[0], "lon": coords[1]})

    # If not in DB, try OSM
    coords = fetch_from_osm(location)
    if coords:
        # Save for future
        save_location_to_db(location, coords[0], coords[1])
        return jsonify({"lat": coords[0], "lon": coords[1]})

    return jsonify({"error": "Coordinates not found"}), 404


@app.route('/get_locations', methods=['GET'])
def get_locations():
    """Return the list of locations used by the model (for populating the dropdown)."""
    global locations
    # If locations were not loaded at startup, try to read columns.json now
    if not locations:
        try:
            if os.path.exists(columns_file):
                with open(columns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    cols = data.get('data_columns', [])
                    if len(cols) > 3:
                        locations = cols[3:]
        except Exception as e:
            print(f"❌ Failed to load locations from columns file: {e}")

    return jsonify({"locations": locations})
cache = {}


@app.route('/get_nearby_places', methods=['GET'])
def get_nearby_places():
    """Query Overpass API for nearby amenities around lat/lon."""
    print("🔍 Starting nearby places search...")
    
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    place_type = request.args.get('type') or request.args.get('place_type') or 'amenity'
    
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except Exception:
        return jsonify({"error": "Invalid or missing lat/lon parameters"}), 400

    print(f"📍 Searching near: {lat_f}, {lon_f} for type: {place_type}")
    
    # radius in meters (increase for better coverage)
    requested_radius = int(request.args.get('radius', 5000))
    # allow up to 10km (10000 m)
    if requested_radius <= 0:
        radius = 5000
    else:
        radius = min(requested_radius, 10000)
    if requested_radius > 10000:
        print(f"⚠️ Requested radius {requested_radius}m exceeds 10000m; using 10000m cap.")

    # optional sorting param (default: distance)
    sort_by = request.args.get('sort', 'distance')

    # Haversine distance (meters)
    from math import radians, sin, cos, sqrt, atan2
    def haversine_meters(lat1, lon1, lat2, lon2):
        # approximate radius of earth in meters
        R = 6371000
        phi1 = radians(lat1)
        phi2 = radians(lat2)
        dphi = radians(lat2 - lat1)
        dlambda = radians(lon2 - lon1)
        a = sin(dphi/2.0)**2 + cos(phi1)*cos(phi2)*sin(dlambda/2.0)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c
    
    # Map simple type keywords to Overpass filters
    filters = []
    t = place_type.lower()
    
    if t == 'school':
        filters = [
            '[amenity~"school|college|university|kindergarten"]',
            '[building~"school|college|university|education"]',
            '[education=*]'
        ]
    elif t == 'hospital':
        filters = [
            '[amenity~"hospital|clinic|doctors|healthcare"]',
            '[healthcare=*]',
            '[medical=*]',
            '[building=hospital]',
            '[amenity=pharmacy]',
            '[shop=pharmacy]'
        ]
    elif t == 'restaurant':
        filters = [
            '[amenity~"restaurant|cafe|fast_food|food_court"]',
            '[cuisine=*]',
            '[shop~"food|bakery"]'
        ]
    elif t == 'mall':
        filters = [
            '[shop~"mall|department_store|supermarket"]',
            '[amenity=marketplace]',
            '[building=retail]',
            '[building=commercial]'
        ]
    else:
        # Generic: try multiple tag types
        filters = [
            f'[amenity={t}]',
            f'[building={t}]',
            f'[shop={t}]'
        ]

    # Build Overpass QL query using 'around' (radius in meters) to avoid bbox formatting issues
    # We'll search nodes, ways and relations for each filter around the given lat/lon
    parts = []
    for flt in filters:
        # normalize filter string (remove surrounding brackets if present)
        f_inner = flt.strip()
        if f_inner.startswith('[') and f_inner.endswith(']'):
            f_inner = f_inner[1:-1]
        # add node/way/relation parts
        parts.append(f"node(around:{radius},{lat_f},{lon_f})[{f_inner}];")
        parts.append(f"way(around:{radius},{lat_f},{lon_f})[{f_inner}];")
        parts.append(f"relation(around:{radius},{lat_f},{lon_f})[{f_inner}];")

    overpass_query = f"[out:json][timeout:60];({''.join(parts)})\nout center qt;"
    print(f"📝 Overpass query (using around): {overpass_query}")

    overpass_endpoints = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter"
    ]

    elements = []
    last_error = None
    
    for overpass_url in overpass_endpoints:
        try:
            print(f"🔎 Querying Overpass at {overpass_url}")
            headers = {'User-Agent': 'Bangalore Property App/1.0'}
            resp = requests.post(overpass_url, 
                              data={"data": overpass_query}, 
                              headers=headers,
                              timeout=30)
            resp.raise_for_status()
            data = resp.json()
            elements = data.get('elements', [])
            if elements:
                print(f"✅ Found {len(elements)} results from {overpass_url}")
                break
            print(f"⚠️ No results from {overpass_url}")
        except Exception as e:
            # Try to print response content when available for debugging
            extra = ''
            resp_obj = getattr(e, 'response', None)
            try:
                if resp_obj is not None and hasattr(resp_obj, 'text'):
                    extra = f" Response text: {resp_obj.text[:500]}"
            except Exception:
                pass
            print(f"⚠️ Overpass endpoint {overpass_url} failed: {e}{extra}")
            last_error = e


    places = []
    for el in elements:
        try:
            tags = el.get('tags', {}) or {}
            # Get name from various possible tags
            name = (tags.get('name') or 
                   tags.get('operator') or 
                   tags.get('brand') or 
                   tags.get('healthcare') or 
                   tags.get('amenity') or 
                   'Unnamed ' + place_type.title())
            
            # get coordinates: node has lat/lon, way/relation may have 'center'
            if el.get('lat') is not None and el.get('lon') is not None:
                plat = float(el.get('lat'))
                plon = float(el.get('lon'))
            else:
                center = el.get('center') or {}
                plat = float(center.get('lat'))
                plon = float(center.get('lon'))
                if plat is None or plon is None:
                    continue

            # Additional details for better identification
            details = []
            if tags.get('healthcare'):
                details.append(tags['healthcare'])
            if tags.get('amenity'):
                details.append(tags['amenity'])
            if tags.get('medical_system'):
                details.append(tags['medical_system'])
                
            description = ' - '.join(filter(None, details))
            if description:
                name = f"{name} ({description})"

            # compute distance and include it
            try:
                dist_m = haversine_meters(lat_f, lon_f, plat, plon)
            except Exception:
                dist_m = None

            places.append({
                "name": name,
                "lat": plat,
                "lon": plon,
                "type": place_type,
                "distance_m": round(dist_m, 2) if dist_m is not None else None
            })
        except (TypeError, ValueError) as e:
            print(f"⚠️ Error processing element: {e}")
            continue

    # Deduplicate by (lat,lon,name) and limit results
    seen = set()
    deduped = []
    for p in places:
        key = (round(float(p['lat']), 5), round(float(p['lon']), 5), p['name'])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(p)
        if len(deduped) >= 50:
            break

    print(f"✅ Found {len(deduped)} places for type={place_type} within {radius}m")

    # Use deduped results as starting point; if too few results, try Nominatim fallback
    final_places = list(deduped)

    if len(final_places) < 5:
        print(f"⚠️ Few results from Overpass API, trying Nominatim for additional places...")
        try:
            # compute approximate degree delta for given radius
            delta = radius / 111000.0  # rough conversion from meters to degrees
            left = lon_f - delta
            right = lon_f + delta
            top = lat_f + delta
            bottom = lat_f - delta
            
            # Map our types to Nominatim categories
            nom_type = place_type
            if place_type == 'hospital':
                nom_type = 'healthcare'
            elif place_type == 'restaurant':
                nom_type = 'food'
            elif place_type == 'mall':
                nom_type = 'shop'
                
            # Use Nominatim keyword search bounded by the viewbox. Nominatim does not support
            # an 'amenity' parameter for search, so use 'q' with the place type.
            nom_params = {
                'q': nom_type,
                'format': 'json',
                'limit': 50,
                'viewbox': f"{left},{top},{right},{bottom}",
                'bounded': 1
            }

            # Try Nominatim search (keyword) within the bounding box
            nom_resp = requests.get(NOMINATIM_API_URL, params=nom_params, timeout=20, headers={'User-Agent': 'Bangalore Property App/1.0'})
            nom_resp.raise_for_status()
            nom_data = nom_resp.json()
            
            # If no results, try a looser keyword search without strict bounding to increase recall
            if not nom_data:
                nom_params = {
                    'q': f"{place_type}",
                    'format': 'json',
                    'limit': 50
                }
                nom_resp = requests.get(NOMINATIM_API_URL, params=nom_params, timeout=20, headers={'User-Agent': 'Bangalore Property App/1.0'})
                nom_resp.raise_for_status()
                nom_data = nom_resp.json()
            
            for item in nom_data:
                try:
                    plat = float(item.get('lat'))
                    plon = float(item.get('lon'))
                    # Extract just the main part of the name, not the full address
                    display_name = item.get('display_name', '').split(',')[0]
                    name = display_name or f"Unnamed {place_type.title()}"
                    
                    # compute distance and include it
                    try:
                        dist_m = haversine_meters(lat_f, lon_f, plat, plon)
                    except Exception:
                        dist_m = None

                    places.append({
                        'name': name,
                        'lat': plat,
                        'lon': plon,
                        'type': place_type,
                        'distance_m': round(dist_m, 2) if dist_m is not None else None
                    })
                except (TypeError, ValueError) as e:
                    print(f"⚠️ Error processing Nominatim result: {e}")
                    continue
                    
            print(f"✅ Added {len(nom_data)} places from Nominatim")

            # merge nominatim results into final_places and deduplicate
            all_places = final_places + places
            seen = set()
            merged = []
            for p in all_places:
                try:
                    key = (round(float(p['lat']), 5), round(float(p['lon']), 5), p.get('name'))
                except Exception:
                    continue
                if key in seen:
                    continue
                seen.add(key)
                merged.append(p)
                if len(merged) >= 50:
                    break
            final_places = merged

        except Exception as e:
            print(f"⚠️ Nominatim search failed: {e}")
            # keep what we have in final_places

    if not final_places:
        print("⚠️ No places found from either source")
        return jsonify({"places": []})

    # Sort results by distance (default) or other criteria
    try:
        if sort_by == 'distance':
            final_places.sort(key=lambda x: (x.get('distance_m') is None, x.get('distance_m', float('inf'))))
        elif sort_by == 'name':
            final_places.sort(key=lambda x: (x.get('name') or '').lower())
    except Exception as e:
        print(f"⚠️ Error sorting final_places: {e}")

    print(f"✅ Returning {len(final_places)} total places after deduplication")
    return jsonify({"places": final_places})
@app.route("/save_favorite", methods=["POST"])
@login_required
def save_favorite():
    data = request.get_json()

    new_fav = Favorite(
        user_id=current_user.id,
        location=data["location"],
        sqft=data["sqft"],
        bhk=data["bhk"],
        bath=data["bath"],
        property_age=data["propertyAge"],
        price=data["price"]
    )
    db.session.add(new_fav)
    db.session.commit()
    return jsonify({"message": "Property saved to favorites!"})

@app.route("/get_favorites", methods=["GET"])
@login_required
def get_favorites():
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    
    fav_list = [{
        "id": fav.id,
        "location": fav.location,
        "sqft": fav.sqft,
        "bhk": fav.bhk,
        "bath": fav.bath,
        "property_age": fav.property_age,
        "price": fav.price
    } for fav in favorites]

    return jsonify({"favorites": fav_list})

@app.route("/delete_favorite/<int:fav_id>", methods=["DELETE"])
@login_required
def delete_favorite(fav_id):
    favorite = Favorite.query.get_or_404(fav_id)
    if favorite.user_id != current_user.id:
        return jsonify({"error": "Unauthorized"}), 403

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"message": "Favorite deleted successfully"})


#create authentication routes
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    existing_user = User.query.filter_by(email=data["email"]).first()
    if existing_user:
        return jsonify({"error": "User already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(data["password"]).decode('utf-8')
    
    new_user = User(name=data["name"], email=data["email"], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"message": "User registered successfully!"})

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if user and bcrypt.check_password_hash(user.password, data["password"]):
        login_user(user)
        return jsonify({"message": "Login successful", "user": user.name})
    
    return jsonify({"error": "Invalid email or password"}), 401

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logged out successfully"})

@app.route("/check_session", methods=["GET"])
def check_session():
    if current_user.is_authenticated:
        return jsonify({"logged_in": True, "user": current_user.name})
    return jsonify({"logged_in": False})


    
# Ensure database tables exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)