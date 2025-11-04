import requests
import csv
import time

OSM_URL = "https://nominatim.openstreetmap.org/search"

def get_coordinates(location):
    """Fetch latitude and longitude from OpenStreetMap Nominatim API."""
    params = {"q": location, "format": "json", "limit": 1}
    headers = {"User-Agent": "LocationFetcher/1.0"}  # Required to prevent blocking
    
    try:
        response = requests.get(OSM_URL, params=params, headers=headers)
        response.raise_for_status()
        data = response.json()
        
        if data:
            lat = float(data[0]["lat"])
            lon = float(data[0]["lon"])
            print(f"✅ {location}: {lat}, {lon}")
            return lat, lon
        else:
            print(f"❌ No data found for {location}")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching {location}: {e}")
        return None, None

# Read locations from CSV and get coordinates
with open("locations.csv", "r") as infile, open("locations_with_coords.csv", "w") as outfile:
    reader = csv.reader(infile)
    writer = csv.writer(outfile)
    
    writer.writerow(["location", "latitude", "longitude"])  # CSV Header
    next(reader)  # Skip header in input file
    
    for row in reader:
        location = row[0]
        lat, lon = get_coordinates(location)
        writer.writerow([location, lat, lon])
        time.sleep(1)  # Prevents API rate limit

print("✅ All locations processed. Saved to locations_with_coords.csv!")
