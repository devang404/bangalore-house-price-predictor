import json

# Load the saved columns.json
with open("columns.json", "r") as f:
    data_columns = json.load(f)["data_columns"]

# Print length and a preview
print("📦 Total features in columns.json:", len(data_columns))
print("🔍 First 10 columns:", data_columns[:10])
print("🔍 Last 10 columns:", data_columns[-10:])
import pickle

with open("banglore_home_prices_model.pickle", "rb") as f:
    model = pickle.load(f)

print("✅ Model expects:", model.n_features_in_, "features")
