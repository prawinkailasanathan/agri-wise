"""
Download and inspect Kaggle dataset: arjunyadav99/indian-agriculture-crop-production-and-yield
"""

import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import os
import shutil
import kagglehub
import pandas as pd

print("Downloading dataset from Kaggle via kagglehub...")
path = kagglehub.dataset_download("arjunyadav99/indian-agriculture-crop-production-and-yield")
print("Path to downloaded dataset files:", path)

# List files
files = os.listdir(path)
print("Files in downloaded dataset:", files)

target_dir = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(target_dir, exist_ok=True)

for f in files:
    src = os.path.join(path, f)
    dst = os.path.join(target_dir, f)
    print(f"Copying {f} to {dst} ...")
    if os.path.isfile(src):
        shutil.copy2(src, dst)
        
        # If it's a CSV, inspect shape and columns
        if f.endswith(".csv"):
            df = pd.read_csv(dst, nrows=10)
            print(f"\n--- Overview of {f} ---")
            print("Columns:", list(df.columns))
            print("Shape of preview:", df.shape)
            print("Head:")
            print(df.head(3))

print("\nDataset preparation completed successfully!")
