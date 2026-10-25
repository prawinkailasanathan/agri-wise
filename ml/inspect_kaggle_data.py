"""
Inspect Kaggle Indian Crop Production & Yield Dataset
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
import pandas as pd

csv_path = os.path.join(os.path.dirname(__file__), "data", "Indian_crop_production_yield_dataset.csv")
df = pd.read_csv(csv_path)

print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")
print("\nMissing values:")
print(df.isnull().sum())

print(f"\nUnique States: {df['State_Name'].nunique()}")
print(f"Unique Districts: {df['District_Name'].nunique()}")
print(f"Unique Crops: {df['Crop'].nunique()}")
print(f"Unique Seasons: {df['Season'].unique()}")

# Crops list sample
print("\nTop 30 Crops:")
print(df["Crop"].value_counts().head(30))

print("\nSummary statistics:")
print(df[["Area", "Production", "yield"]].describe())

# Check for crops matching AgriWise crops
agriwise_crops = ['Tomato', 'Onion', 'Potato', 'Brinjal', 'Cabbage', 'Cauliflower', 'Beans', 'Carrot', 'Radish', 'Coriander']
print("\nMatches with AgriWise vegetable crops:")
for c in agriwise_crops:
    matches = df[df["Crop"].str.contains(c, case=False, na=False)]["Crop"].unique()
    print(f"  {c}: {matches}")
