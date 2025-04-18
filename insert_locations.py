import sqlite3
import csv

# Connect to SQLite database
conn = sqlite3.connect("house_prices.db")
cursor = conn.cursor()

# Ensure the table exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS heatmap_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT UNIQUE,
        latitude REAL,
        longitude REAL,
        avg_price REAL DEFAULT 0  -- Ensure avg_price has a default value
    );
""")

# Delete existing locations to prevent duplicates
cursor.execute("DELETE FROM heatmap_data;")

# Read locations from CSV and insert them into the database
with open("locations_with_coords.csv", "r") as file:
    reader = csv.reader(file)
    next(reader)  # Skip header

    for row in reader:
        if len(row) < 3:  # Skip invalid rows
            print(f"⚠️ Skipping invalid row: {row}")
            continue

        location, lat, lon = row[0].strip(), row[1].strip(), row[2].strip()
        avg_price = 0  # Default value (or fetch real price data if available)

        if not location or not lat or not lon:  # Skip empty values
            print(f"⚠️ Skipping incomplete row: {row}")
            continue

        try:
            lat, lon = float(lat), float(lon)  # Convert to float
            cursor.execute("INSERT INTO heatmap_data (location, latitude, longitude, avg_price) VALUES (?, ?, ?, ?)", 
                           (location, lat, lon, avg_price))
        except ValueError:
            print(f"⚠️ Skipping row with invalid numbers: {row}")
            continue

# Commit and close connection
conn.commit()
conn.close()
print("✅ All locations reinserted into the database!")
