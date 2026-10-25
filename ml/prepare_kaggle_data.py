"""
AgriWise - Preprocess and Enrich Kaggle Dataset:
arjunyadav99/indian-agriculture-crop-production-and-yield

Cleans 575,000+ real records, maps standard crop names, removes agronomic outliers,
and enriches with place-based market demand and APMC price dynamics.
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
import numpy as np
import pandas as pd

raw_csv = os.path.join(os.path.dirname(__file__), "data", "Indian_crop_production_yield_dataset.csv")
out_csv = os.path.join(os.path.dirname(__file__), "data", "kaggle_crop_production_demand.csv")

print(f"Loading raw Kaggle dataset from: {raw_csv}")
df = pd.read_csv(raw_csv)
print(f"Raw shape: {df.shape}")

# Standardize whitespace and case
df["State_Name"] = df["State_Name"].astype(str).str.strip().str.title()
df["District_Name"] = df["District_Name"].astype(str).str.strip().str.title()
df["Season"] = df["Season"].astype(str).str.strip()
df["Crop"] = df["Crop"].astype(str).str.strip()

# Crop Name Normalization for AgriWise
CROP_MAP = {
    "Tomato": "Tomato",
    "Onion": "Onion",
    "Potato": "Potato",
    "Sweet Potato": "Sweet Potato",
    "Brinjal": "Brinjal",
    "Cabbage": "Cabbage",
    "Cauliflower": "Cauliflower",
    "Bhindi": "Lady's Finger",
    "Drum Stick": "Drumstick",
    "Redish": "Radish",
    "Carrot": "Carrot",
    "Coriander": "Coriander",
    "Dry Chillies": "Green Chilli",
    "Beans & Mutter(Vegetable)": "Beans",
    "Bean": "Beans",
    "Peas  (Vegetable)": "Beans",
    "Garlic": "Garlic",
    "Ginger": "Ginger",
    "Dry Ginger": "Ginger",
    "Turmeric": "Turmeric",
    "Bitter Gourd": "Bitter Gourd",
    "Bottle Gourd": "Bottle Gourd",
    "Cucumber": "Cucumber",
    "Water Melon": "Water Melon",
    "Banana": "Banana"
}

# Focus on vegetables and commercial horticulture
target_raw_crops = list(CROP_MAP.keys())
df_target = df[df["Crop"].isin(target_raw_crops)].copy()
df_target["Standard_Crop"] = df_target["Crop"].map(CROP_MAP)

print(f"Filtered to target vegetables and crops: {len(df_target)} records")

# Cleaning outliers according to agronomic feasibility (tonnes/ha)
# Yields above 100 t/ha for vegetables are recording errors in government entries
df_clean = df_target[
    (df_target["Area"] > 0.05) &
    (df_target["Area"] < 100000) &
    (df_target["Production"] > 0) &
    (df_target["yield"] > 0.1) &
    (df_target["yield"] < 85.0)
].copy()

print(f"After removing zero/corrupt yield outliers: {len(df_clean)} records")

# Base price index (₹/kg) and market demand profiles per crop
BASE_CROP_PRICES = {
    "Tomato": 22.0, "Onion": 25.0, "Potato": 18.0, "Sweet Potato": 20.0,
    "Brinjal": 25.0, "Cabbage": 22.0, "Cauliflower": 30.0, "Lady's Finger": 40.0,
    "Drumstick": 38.0, "Radish": 16.0, "Carrot": 35.0, "Coriander": 95.0,
    "Green Chilli": 55.0, "Beans": 48.0, "Garlic": 110.0, "Ginger": 80.0,
    "Turmeric": 70.0, "Bitter Gourd": 32.0, "Bottle Gourd": 20.0,
    "Cucumber": 22.0, "Water Melon": 15.0, "Banana": 25.0
}

# Top consumption / urban states having higher local market demand
URBAN_STATES = {
    "Maharashtra": 1.25, "Karnataka": 1.20, "Tamil Nadu": 1.18,
    "West Bengal": 1.22, "Uttar Pradesh": 1.15, "Gujarat": 1.15,
    "Punjab": 1.12, "Delhi": 1.45, "Kerala": 1.20, "Telangana": 1.20,
    "Andhra Pradesh": 1.10, "Madhya Pradesh": 1.08, "Bihar": 1.05
}

# Add realistic Demand & Price modeling based on place & supply
np.random.seed(42)

demands = []
prices = []
demand_categories = []

for idx, row in df_clean.iterrows():
    crop = row["Standard_Crop"]
    state = row["State_Name"]
    area = row["Area"]
    prod = row["Production"]
    crop_yield = row["yield"]
    
    base_p = BASE_CROP_PRICES.get(crop, 25.0)
    state_demand_factor = URBAN_STATES.get(state, 1.05)
    
    # Calculate localized supply pressure:
    # High production in a district leads to harvest peaks and lower spot prices
    # Moderate production keeps market in high demand
    expected_yield = 18.0
    supply_intensity = crop_yield / expected_yield
    
    # Place-based Demand Index (0 to 100):
    # Driven by state urban factor, modulated inversely by local supply glut
    raw_demand = (52.0 * state_demand_factor) / (supply_intensity ** 0.45)
    raw_demand += np.random.normal(0, 3.5)
    demand_idx = float(np.round(np.clip(raw_demand, 15.0, 98.0), 1))
    
    # Demand-to-Supply Ratio
    ratio = (demand_idx / 50.0) / (supply_intensity ** 0.7)
    
    # Dynamic Mandi Price (₹/kg)
    price_elasticity = 0.32
    price_mult = (ratio ** price_elasticity) * np.random.normal(1.0, 0.04)
    mandi_price = float(np.round(np.clip(base_p * price_mult, 8.0, 220.0), 2))
    
    if demand_idx >= 68:
        category = "High"
    elif demand_idx >= 45:
        category = "Moderate"
    else:
        category = "Oversupplied"
        
    demands.append(demand_idx)
    prices.append(mandi_price)
    demand_categories.append(category)

df_clean["Demand_Index"] = demands
df_clean["Mandi_Price_Rs_Per_Kg"] = prices
df_clean["Demand_Category"] = demand_categories

# Rename columns cleanly
df_clean = df_clean.rename(columns={
    "State_Name": "State",
    "District_Name": "District",
    "Crop_Year": "Year",
    "Area": "Area_Hectares",
    "Production": "Production_Tonnes",
    "yield": "Yield_Tonnes_Per_Ha",
    "Standard_Crop": "Crop_Name"
})

output_cols = [
    "State", "District", "Crop_Name", "Season", "Year",
    "Area_Hectares", "Production_Tonnes", "Yield_Tonnes_Per_Ha",
    "Demand_Index", "Mandi_Price_Rs_Per_Kg", "Demand_Category"
]
df_final = df_clean[output_cols].copy()

# Sample down slightly if too large, or keep balanced sample of 40,000 records
if len(df_final) > 40000:
    # Stratified balance across crops
    df_final = df_final.groupby("Crop_Name", group_keys=False).apply(
        lambda x: x.sample(min(len(x), 4500), random_state=42)
    ).reset_index(drop=True)

df_final.to_csv(out_csv, index=False)
print(f"\nFinal enriched dataset saved to: {out_csv}")
print(f"Final Shape: {df_final.shape}")
print(f"Crops included ({df_final['Crop_Name'].nunique()}):", sorted(df_final["Crop_Name"].unique()))
print(f"States included: {df_final['State'].nunique()}, Districts: {df_final['District'].nunique()}")
print("\nSample records:")
print(df_final.head(4))
