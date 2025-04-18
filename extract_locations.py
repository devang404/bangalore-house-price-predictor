import json

# Load locations from columns.json
with open("columns.json", "r") as file:
    data_columns = json.load(file)["data_columns"]

# Extract locations (Skip first 3 columns: sqft, bath, bhk)
locations = data_columns[3:]

# Save locations to a CSV file
with open("locations.csv", "w") as file:
    file.write("location\n")  # CSV Header
    for loc in locations:
        file.write(f"{loc}\n")

print(f"✅ Extracted {len(locations)} locations. Saved to locations.csv!")
