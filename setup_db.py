import sqlite3

# Function to connect to the SQLite database
def get_db_connection():
    conn = sqlite3.connect("house_prices.db")
    return conn

# Function to create required tables
def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create price_trends table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS price_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            date TEXT NOT NULL,
            avg_price REAL NOT NULL
        )
    """)

    # Create heatmap_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heatmap_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            avg_price REAL NOT NULL
        )
    """)

    conn.commit()
    conn.close()
    print("✅ Tables created successfully!")

# Function to insert sample data
def insert_sample_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert sample price trends
    sample_price_trends = [
        ("Ambalipura", "2024-01", 5500000),
        ("Ambalipura", "2024-02", 5600000),
        ("Ambalipura", "2024-03", 5700000),
        ("HSR Layout", "2024-01", 7500000),
        ("HSR Layout", "2024-02", 7600000),
        ("HSR Layout", "2024-03", 7700000)
    ]
    
    cursor.executemany("INSERT INTO price_trends (location, date, avg_price) VALUES (?, ?, ?)", sample_price_trends)

    # Insert sample heatmap data
    sample_heatmap_data = [
        ("Ambalipura", 12.9121, 77.6446, 5700000),
        ("HSR Layout", 12.9113, 77.6388, 7700000),
        ("Bellandur", 12.9352, 77.6736, 8500000),
        ("Electronic City", 12.8392, 77.6793, 4500000)
    ]

    cursor.executemany("INSERT INTO heatmap_data (location, latitude, longitude, avg_price) VALUES (?, ?, ?, ?)", sample_heatmap_data)

    conn.commit()
    conn.close()
    print("✅ Sample data inserted successfully!")

# Run the functions
if __name__ == "__main__":
    create_tables()
    insert_sample_data()
    print("✅ Database setup complete!")
