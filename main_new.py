import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import json

# 🔹 Load Dataset
df = pd.read_csv("BHP.csv")

# Clean and preprocess
df.drop(["area_type", "society", "balcony", "availability"], axis=1, inplace=True)
df.dropna(inplace=True)

# Extract BHK and convert sqft
df["bhk"] = df["size"].apply(lambda x: int(x.split(' ')[0]) if isinstance(x, str) else None)
df.dropna(subset=["bhk"], inplace=True)
df.drop("size", axis=1, inplace=True)

def convert_sqft(sqft):
    try:
        if '-' in sqft:
            a, b = map(float, sqft.split('-'))
            return (a + b) / 2
        return float(sqft)
    except:
        return None

df["total_sqft"] = df["total_sqft"].apply(convert_sqft)
df.dropna(subset=["total_sqft"], inplace=True)
df = df[df["total_sqft"] / df["bhk"] >= 300]

# Add synthetic property age with stronger impact
np.random.seed(42)
df["property_age"] = np.random.randint(0, 21, size=len(df))
age_impact = 1 - (df["property_age"] / 20) * 0.4  # 40% reduction for oldest properties
df["price"] = df["price"] * age_impact

# Define location tiers with much stronger price effects
location_tiers = {
    'premium': ['Indiranagar', 'Whitefield', 'Koramangala', 'Richmond Town', 'Lavelle Road'],
    'high': ['HSR Layout', 'Jayanagar', 'JP Nagar', 'Malleshwaram', 'Sadashivanagar'],
    'mid': ['Electronic City', 'Yelahanka', 'Hebbal', 'Bannerghatta', 'Marathahalli'],
    'budget': []  # All others
}

# Create location tier mapping
df['location_tier'] = df['location'].apply(
    lambda x: 4 if x in location_tiers['premium']
    else 3 if x in location_tiers['high']
    else 2 if x in location_tiers['mid']
    else 1
)

# Apply much stronger location-based price adjustments
tier_multipliers = {4: 2.0, 3: 1.5, 2: 1.2, 1: 1.0}
df['price'] = df['price'] * df['location_tier'].map(tier_multipliers)

# Calculate price per sqft after adjustments
df['price_per_sqft'] = df['price'] * 100000 / df['total_sqft']

# Add engineered features
df['age_factor'] = 1 - (df['property_age'] / 20) * 0.4
df['location_score'] = df['location_tier'] / 4  # Normalize to 0-1
df['size_score'] = (df['total_sqft'] - df['total_sqft'].min()) / (df['total_sqft'].max() - df['total_sqft'].min())

# Composite features
df['quality_score'] = (df['location_score'] * 0.5 + df['age_factor'] * 0.3 + df['size_score'] * 0.2) * 100
df['price_index'] = df['price_per_sqft'] * df['quality_score'] / 100

# One-hot encode locations (preserve premium locations)
location_dummies = pd.get_dummies(df['location'])
df = pd.concat([
    df.drop(['location', 'location_tier', 'location_score', 'size_score'], axis=1),
    location_dummies
], axis=1)

# Train/test split and scale
X = df.drop('price', axis=1)
y = df['price']

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Train with more complex model
model = RandomForestRegressor(
    n_estimators=1000,
    max_depth=20,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42
)
model.fit(X_train, y_train)

# Save artifacts
with open("banglore_home_prices_model.pickle", "wb") as f:
    pickle.dump(model, f)
with open("columns.json", "w") as f:
    json.dump({"data_columns": list(X.columns)}, f)

# Report results
print(f"\n✅ Model Training Completed. Accuracy Score: {model.score(X_test, y_test):.4f}")
importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
print("\n🏆 Top 10 Important Features:")
print(importances.head(10).to_string())