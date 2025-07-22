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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # Prevents warning
app.config['SECRET_KEY'] = 'your_secret_key'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = "info"  # Flash message category
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"
CORS(app)

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

    # Extract locations (assuming first 4 columns are fixed: sqft, bath, bhk, property_age)
    locations = data_columns[4:]

    print(f"✅ Model and {len(locations)} locations loaded successfully!")

except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None
    data_columns = []
    locations = []



class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    sqft = db.Column(db.Float, nullable=False)
    bhk = db.Column(db.Integer, nullable=False)
    bath = db.Column(db.Integer, nullable=False)
    property_age = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    user = db.relationship('User', backref=db.backref('favorites', lazy=True))



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
def home():
    return render_template("app.html")

@app.route("/get_locations", methods=["GET"])
def get_locations():
    return jsonify({"locations": locations})

@app.route("/login_page")
def login_page():
    return render_template("login.html")

@app.route("/register_page")
def register_page():
    return render_template("register.html")



@app.route("/predict_price", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        print("📥 Received Data for Prediction:", data)

        if model is None or data_columns is None:
            return jsonify({"error": "Model or data columns not loaded."}), 500

        # Create zero vector of length equal to number of features
        features = np.zeros(len(data_columns))

        # Fill in numeric features
        features[data_columns.index("total_sqft")] = float(data.get("total_sqft", 0))
        features[data_columns.index("bath")] = int(data.get("bath", 0))
        features[data_columns.index("property_age")] = int(data.get("property_age", 0))
        features[data_columns.index("bhk")] = int(data.get("bhk", 0))

        # Handle location (case-sensitive if saved that way)
        location = data.get("location", "")
        if location in data_columns:
            loc_index = data_columns.index(location)
            features[loc_index] = 1
        else:
            print(f"⚠️ Location '{location}' not found in model's data columns.")

        # Prediction
        prediction = model.predict([features])[0]
        print("💰 Predicted Price:", prediction)

        return jsonify({"estimated_price": round(prediction, 2)})

    except Exception as e:
        print(f"❌ Error in Prediction: {str(e)}")
        return jsonify({"error": str(e)}), 500


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

    cursor.execute("INSERT INTO heatmap_data (location, latitude, longitude) VALUES (?, ?, ?)", (location_name.strip(), lat, lon))
    conn.commit()
    conn.close()
    print(f"✅ Saved {location_name} to database!")

@app.route("/get_location_coords", methods=["GET"])
def get_location_coords():
    location = request.args.get("location", "").strip()

    if not location:
        return jsonify({"error": "Location not provided"}), 400

    # ✅ First, check database
    coords = get_location_from_db(location)
    if coords:
        return jsonify({"lat": coords[0], "lon": coords[1]})

    # 🌍 Fetch from OpenStreetMap if not in database
    coords = fetch_from_osm(location)
    if coords:
        save_location_to_db(location, coords[0], coords[1])  # 🔥 Auto-save for future use
        return jsonify({"lat": coords[0], "lon": coords[1]})

    return jsonify({"error": "Location not found"}), 404

# Function to fetch house prices from the SQLite database
@app.route("/get_house_prices", methods=["GET"])
def get_house_prices():
    conn = sqlite3.connect("users.db")  # Replace with your actual database file name
    cursor = conn.cursor()

    # Assuming your table is named 'properties' with columns: id, latitude, longitude, price
    cursor.execute("SELECT latitude, longitude, price FROM properties")
    rows = cursor.fetchall()
    conn.close()

    # Convert data to JSON format for the heatmap
    house_prices = [{"lat": row[0], "lng": row[1], "price": row[2]} for row in rows]

    return jsonify(house_prices)


@app.route("/get_price_chart_data", methods=["GET"])
def get_price_chart_data():
    # Sample data: Fetch actual price trends from your database
    price_chart_data = {
        "locations": ["HSR Layout", "Indiranagar", "Whitefield", "Jayanagar"],
        "prices": [120, 150, 95, 110]  # Prices in Lakhs
    }
    return jsonify(price_chart_data)

#mapping location and nearby amenities
cache={}
@app.route('/get_nearby_places', methods=['GET'])
def get_nearby_places():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    place_type = request.args.get('type')
    
    
    if not lat or not lon or not place_type:
        return jsonify({"error": "Missing parameters"}), 400
    
    overpass_query = f"""
[out:json][timeout:10];
(
  node["amenity"="{place_type}"](around:1500,{lat},{lon});
);
out body;
"""
    # Construct the API request URL (Example using OpenStreetMap Overpass API)
    overpass_url = f"https://overpass-api.de/api/interpreter?data=[out:json];node[amenity={place_type}](around:2000,{lat},{lon});out;"

    print("Fetching from:", overpass_url)  # Debugging Line

    try:
        response = requests.get(overpass_url,params={"data": overpass_query})
        print("Response Status Code:", response.status_code)  # Debugging Line
        print("Response Content:", response.text)  # Debugging Line

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch data from Overpass API"}), 500

        data = response.json()  # Try parsing JSON
        places = []
        for element in data.get('elements', []):
            if 'lat' in element and 'lon' in element and 'tags' in element:
                places.append({
                    "name": element['tags'].get('name', 'Unknown'),
                    "lat": element['lat'],
                    "lon": element['lon']
                })

        return jsonify({"places": places})

    except requests.exceptions.RequestException as e:
        print("Request Error:", e)  # Debugging Line
        return jsonify({"error": "Request failed"}), 500
    except ValueError as e:
        print("JSON Decode Error:", e)  # Debugging Line
        return jsonify({"error": "Invalid JSON response"}), 500
    

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



    
if __name__ == "__main__":
    with app.app_context():
        db.create_all()


    app.run(debug=True)
