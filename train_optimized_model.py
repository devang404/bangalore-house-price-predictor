
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import pickle
import json
import os

# 1. Load Data
print("⏳ Loading data...")
try:
    df = pd.read_csv("BHP.csv")
    print(f"✅ Data loaded. Shape: {df.shape}")
except FileNotFoundError:
    print("❌ BHP.csv not found!")
    exit()

# 2. Data Cleaning & Feature Engineering
print("🧹 Cleaning data...")

# Drop unnecessary columns
df2 = df.drop(['area_type', 'society', 'balcony', 'availability'], axis='columns')

# Handle missing values
df3 = df2.dropna()

# Function to convert 'total_sqft' to float
def convert_sqft_to_num(x):
    tokens = str(x).split('-')
    if len(tokens) == 2:
        return (float(tokens[0]) + float(tokens[1])) / 2
    try:
        return float(x)
    except:
        return None

df4 = df3.copy()
df4['total_sqft'] = df4['total_sqft'].apply(convert_sqft_to_num)

# Extract BHK from size
df4['bhk'] = df4['size'].apply(lambda x: int(x.split(' ')[0]))

df4 = df4.dropna() 

# Feature Engineering: Price per sqft (for outlier removal)
df5 = df4.copy()
df5['price_per_sqft'] = df5['price'] * 100000 / df5['total_sqft']

# Dimensionality Reduction: Location
df5['location'] = df5['location'].apply(lambda x: x.strip())
location_stats = df5['location'].value_counts(ascending=False)
location_stats_less_than_10 = location_stats[location_stats <= 10]
df5['location'] = df5['location'].apply(lambda x: 'other' if x in location_stats_less_than_10 else x)

# Outlier Removal
df6 = df5[~(df5.total_sqft / df5.bhk < 300)]

def remove_pps_outliers(df):
    df_out = pd.DataFrame()
    for key, subdf in df.groupby('location'):
        m = np.mean(subdf.price_per_sqft)
        st = np.std(subdf.price_per_sqft)
        reduced_df = subdf[(subdf.price_per_sqft > (m - st)) & (subdf.price_per_sqft <= (m + st))]
        df_out = pd.concat([df_out, reduced_df], ignore_index=True)
    return df_out

df7 = remove_pps_outliers(df6)

def remove_bhk_outliers(df):
    exclude_indices = np.array([])
    for location, location_df in df.groupby('location'):
        bhk_stats = {}
        for bhk, bhk_df in location_df.groupby('bhk'):
            bhk_stats[bhk] = {
                'mean': np.mean(bhk_df.price_per_sqft),
                'std': np.std(bhk_df.price_per_sqft),
                'count': bhk_df.shape[0]
            }
        for bhk, bhk_df in location_df.groupby('bhk'):
            stats = bhk_stats.get(bhk - 1)
            if stats and stats['count'] > 5:
                exclude_indices = np.append(exclude_indices, bhk_df[bhk_df.price_per_sqft < (stats['mean'])].index.values)
    return df.drop(exclude_indices, axis='index')

df8 = remove_bhk_outliers(df7)
df9 = df8.drop(['price_per_sqft'], axis='columns')

# One Hot Encoding
dummies = pd.get_dummies(df9.location)
df10 = pd.concat([df9, dummies.drop('other', axis='columns')], axis='columns')
df11 = df10.drop(['location', 'size'], axis='columns')

print(f"✅ Preprocessing done. Final Shape: {df11.shape}")

# 3. Model Training
X = df11.drop('price', axis='columns')
y = df11.price

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=10)




# Limiting depth and estimators significantly reduces model size.
model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=10, n_jobs=-1)
model.fit(X_train, y_train)

score = model.score(X_test, y_test)
print(f"🎯 Model Accuracy (R^2): {score:.4f}")

# 4. Save Model & Columns
output_model_file = "banglore_home_prices_model.pickle"
with open(output_model_file, 'wb') as f:
    pickle.dump(model, f)

columns = {
    'data_columns': [col.lower() for col in X.columns]
}
with open("columns.json", "w") as f:
    f.write(json.dumps(columns))

# Check size
size_mb = os.path.getsize(output_model_file) / (1024 * 1024)
print(f"📦 Model saved to {output_model_file}")
print(f"START_SIZE:{size_mb:.2f}MB:END_SIZE")
