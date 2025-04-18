import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pickle
import json

# Fix negative prices if any
def transform_negative_prices(df, price_column="price"):
    df_transformed = df.copy()
    min_price = df_transformed[price_column].min()
    if min_price < 0:
        df_transformed[price_column] += abs(min_price) + 1
    df_transformed[price_column] = np.maximum(df_transformed[price_column], 10)
    return df_transformed

# 🔹 Load Dataset
df = pd.read_csv("BHP.csv")

# 🔹 Add Synthetic Property Age (Random between 0-50 years)
np.random.seed(42)
df["property_age"] = np.random.randint(0, 21, size=len(df))
df["price"] *= (1 - df["property_age"] / 100) 

# 🔹 Drop Unnecessary Columns
df.drop(["area_type", "society", "balcony", "availability"], axis=1, inplace=True)
df.dropna(inplace=True)

# 🔹 Extract BHK from "size"
df["bhk"] = df["size"].apply(lambda x: int(x.split(' ')[0]) if isinstance(x, str) else None)
df.dropna(subset=["bhk"], inplace=True)
df.drop("size", axis=1, inplace=True)

# 🔹 Convert total_sqft to float
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

# 🔹 Calculate price_per_sqft
df["price_per_sqft"] = df["price"] * 100000 / df["total_sqft"]

# 🔹 Group low frequency locations as "other"
loc_stats = df["location"].value_counts()
low_freq_loc = loc_stats[loc_stats <= 10].index
df["location"] = df["location"].apply(lambda x: "other" if x in low_freq_loc else x)

# 🔹 One-hot encode locations
location_dummies = pd.get_dummies(df["location"])
df = pd.concat([df.drop("location", axis=1), location_dummies.drop("other", axis=1)], axis=1)

# 🔹 Additional Engineered Features
df["age_per_sqft"] = df["property_age"] / df["total_sqft"]
df["adjusted_sqft"] = df["total_sqft"] * (1 - df["property_age"] / 100)

# 🔹 Define X and y
X = df.drop("price", axis=1)
y = df["price"]

# 🔹 Scale Features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 🔹 Train-Test Split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 🔹 Train Model
model = RandomForestRegressor(n_estimators=300, max_depth=12, random_state=42)
model.fit(X_train, y_train)

# 🔹 Evaluate Feature Importance
importances = model.feature_importances_
columns = X.columns
property_age_importance = importances[columns.get_loc("property_age")]

# 🔹 Save model and data
with open("banglore_home_prices_model.pickle", "wb") as f:
    pickle.dump(model, f)
with open("scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)
with open("columns.json", "w") as f:
    json.dump({"data_columns": list(X.columns)}, f)

# 🔹 Output
# print("\n📊 Feature Importance of 'property_age':", round(property_age_importance, 6))
# sorted_idx = np.argsort(importances)[::-1]
# print("\n🏆 Top 10 Important Features:")
# for i in range(10):
#     print(f"{columns[sorted_idx[i]]}: {importances[sorted_idx[i]]:.6f}")

print(f"\n✅ Model Training Completed. Accuracy Score: {model.score(X_test, y_test):.4f}")



