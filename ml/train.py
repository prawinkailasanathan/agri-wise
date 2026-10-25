"""
AgriWise - Deep Learning Training on Kaggle Indian Agriculture Dataset
Target Formulation:
  1. Yield_Tonnes_Per_Ha (Crop Productivity per hectare for the place/crop/season)
  2. Demand_Index (0 to 100 Market Demand Score for the APMC district)
  3. Mandi_Price_Rs_Per_Kg (Projected equilibrium market price)
Complies with ML Best Practices.
"""

import json
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from model import DeepAgNet

torch.manual_seed(42)
np.random.seed(42)

class AgriKaggleDataset(Dataset):
    def __init__(self, x_cat, x_cont, y_yield, y_demand, y_price):
        self.x_cat = torch.tensor(x_cat, dtype=torch.long)
        self.x_cont = torch.tensor(x_cont, dtype=torch.float32)
        self.y_yield = torch.tensor(y_yield, dtype=torch.float32).unsqueeze(1)
        self.y_demand = torch.tensor(y_demand, dtype=torch.float32).unsqueeze(1)
        self.y_price = torch.tensor(y_price, dtype=torch.float32).unsqueeze(1)

    def __len__(self):
        return len(self.x_cat)

    def __getitem__(self, idx):
        return (
            self.x_cat[idx],
            self.x_cont[idx],
            self.y_yield[idx],
            self.y_demand[idx],
            self.y_price[idx],
        )

def train_kaggle_model():
    data_path = os.path.join(os.path.dirname(__file__), "data", "kaggle_crop_production_demand.csv")
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)

    print(f"Loading Kaggle dataset from: {data_path}")
    df = pd.read_csv(data_path)
    print(f"Total records loaded: {len(df)}")

    cat_cols = ["State", "District", "Crop_Name", "Season"]
    cont_cols = ["Area_Hectares", "Year"]

    # 1. Strict ML Best Practice: Split data BEFORE fitting scalers or encoders
    train_df, test_val_df = train_test_split(df, test_size=0.30, random_state=42)
    val_df, test_df = train_test_split(test_val_df, test_size=0.50, random_state=42)

    print(f"Splits: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")

    # 2. Fit LabelEncoders on Train split only
    label_encoders = {}
    emb_dims = []

    for col in cat_cols:
        le = LabelEncoder()
        le.fit(train_df[col].astype(str))
        label_encoders[col] = le
        num_classes = len(le.classes_)
        emb_dim = min(32, max(4, (num_classes + 1) // 2 + 2))
        emb_dims.append((num_classes, emb_dim))
        print(f"Categorical '{col}': {num_classes} classes -> Embedding Dim: {emb_dim}")

    def encode_cats(subset_df):
        encoded = np.zeros((len(subset_df), len(cat_cols)), dtype=np.int64)
        for i, col in enumerate(cat_cols):
            le = label_encoders[col]
            classes = set(le.classes_)
            encoded[:, i] = subset_df[col].astype(str).apply(lambda x: le.transform([x])[0] if x in classes else 0).values
        return encoded

    # 3. Fit continuous scaler on Train split only
    scaler = StandardScaler()
    scaler.fit(train_df[cont_cols])

    X_train_cat = encode_cats(train_df)
    X_val_cat = encode_cats(val_df)
    X_test_cat = encode_cats(test_df)

    X_train_cont = scaler.transform(train_df[cont_cols])
    X_val_cont = scaler.transform(val_df[cont_cols])
    X_test_cont = scaler.transform(test_df[cont_cols])

    # Targets: Yield (t/ha), Demand (0-100), Price (Rs/kg)
    y_train_yield = train_df["Yield_Tonnes_Per_Ha"].values
    y_val_yield = val_df["Yield_Tonnes_Per_Ha"].values
    y_test_yield = test_df["Yield_Tonnes_Per_Ha"].values

    y_train_demand = train_df["Demand_Index"].values
    y_val_demand = val_df["Demand_Index"].values
    y_test_demand = test_df["Demand_Index"].values

    y_train_price = train_df["Mandi_Price_Rs_Per_Kg"].values
    y_val_price = val_df["Mandi_Price_Rs_Per_Kg"].values
    y_test_price = test_df["Mandi_Price_Rs_Per_Kg"].values

    train_ds = AgriKaggleDataset(X_train_cat, X_train_cont, y_train_yield, y_train_demand, y_train_price)
    val_ds = AgriKaggleDataset(X_val_cat, X_val_cont, y_val_yield, y_val_demand, y_val_price)
    test_ds = AgriKaggleDataset(X_test_cat, X_test_cont, y_test_yield, y_test_demand, y_test_price)

    train_loader = DataLoader(train_ds, batch_size=128, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=256, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=256, shuffle=False)

    # 4. Multi-Task Deep Neural Network
    model = DeepAgNet(emb_dims=emb_dims, num_cont_features=len(cont_cols), hidden_dims=[256, 128, 64], dropout_rate=0.2)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)
    print(f"Training on device: {device}")

    huber_loss = nn.SmoothL1Loss()
    mse_loss = nn.MSELoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=0.003, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", factor=0.5, patience=3)

    num_epochs = 32
    best_val_loss = float("inf")
    best_model_weights = None

    print("\nStarting Model Training on Kaggle Indian Agriculture Dataset...")
    print("-" * 70)

    for epoch in range(1, num_epochs + 1):
        model.train()
        train_loss = 0.0

        for x_cat_b, x_cont_b, y_yield_b, y_dem_b, y_price_b in train_loader:
            x_cat_b = x_cat_b.to(device)
            x_cont_b = x_cont_b.to(device)
            y_yield_b = y_yield_b.to(device)
            y_dem_b = y_dem_b.to(device)
            y_price_b = y_price_b.to(device)

            optimizer.zero_grad()
            p_yield, p_dem, p_price = model(x_cat_b, x_cont_b)

            l_yield = huber_loss(p_yield / 20.0, y_yield_b / 20.0)
            l_dem = mse_loss(p_dem / 50.0, y_dem_b / 50.0)
            l_price = huber_loss(p_price / 30.0, y_price_b / 30.0)

            total_loss = 1.0 * l_yield + 0.8 * l_dem + 1.2 * l_price
            total_loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()

            train_loss += total_loss.item() * len(x_cat_b)

        train_loss /= len(train_ds)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x_cat_b, x_cont_b, y_yield_b, y_dem_b, y_price_b in val_loader:
                x_cat_b = x_cat_b.to(device)
                x_cont_b = x_cont_b.to(device)
                y_yield_b = y_yield_b.to(device)
                y_dem_b = y_dem_b.to(device)
                y_price_b = y_price_b.to(device)

                p_yield, p_dem, p_price = model(x_cat_b, x_cont_b)
                l_yield = huber_loss(p_yield / 20.0, y_yield_b / 20.0)
                l_dem = mse_loss(p_dem / 50.0, y_dem_b / 50.0)
                l_price = huber_loss(p_price / 30.0, y_price_b / 30.0)
                v_loss = 1.0 * l_yield + 0.8 * l_dem + 1.2 * l_price
                val_loss += v_loss.item() * len(x_cat_b)

        val_loss /= len(val_ds)
        scheduler.step(val_loss)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_model_weights = model.state_dict().copy()
            saved_indicator = " [BEST MODEL SAVED]"
        else:
            saved_indicator = ""

        if epoch % 5 == 0 or epoch == 1 or saved_indicator:
            print(f"Epoch {epoch:02d}/{num_epochs:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f} | LR: {optimizer.param_groups[0]['lr']:.5f}{saved_indicator}")

    # Load best weights
    model.load_state_dict(best_model_weights)

    # 5. Evaluate on Hold-out Test Set
    print("\n" + "=" * 70)
    print("Evaluating Model on Hold-Out Test Set (Unseen Kaggle Data)...")
    print("=" * 70)

    model.eval()
    test_preds_yield = []
    test_preds_dem = []
    test_preds_price = []

    with torch.no_grad():
        for x_cat_b, x_cont_b, _, _, _ in test_loader:
            x_cat_b = x_cat_b.to(device)
            x_cont_b = x_cont_b.to(device)
            p_yield, p_dem, p_price = model(x_cat_b, x_cont_b)
            test_preds_yield.extend(p_yield.cpu().numpy().flatten())
            test_preds_dem.extend(p_dem.cpu().numpy().flatten())
            test_preds_price.extend(p_price.cpu().numpy().flatten())

    test_preds_yield = np.array(test_preds_yield)
    test_preds_dem = np.array(test_preds_dem)
    test_preds_price = np.array(test_preds_price)

    # Metrics
    mae_yield = mean_absolute_error(y_test_yield, test_preds_yield)
    rmse_yield = np.sqrt(mean_squared_error(y_test_yield, test_preds_yield))
    r2_yield = r2_score(y_test_yield, test_preds_yield)

    mae_dem = mean_absolute_error(y_test_demand, test_preds_dem)
    rmse_dem = np.sqrt(mean_squared_error(y_test_demand, test_preds_dem))
    r2_dem = r2_score(y_test_demand, test_preds_dem)

    mae_price = mean_absolute_error(y_test_price, test_preds_price)
    rmse_price = np.sqrt(mean_squared_error(y_test_price, test_preds_price))
    r2_price = r2_score(y_test_price, test_preds_price)

    print(f"[RESULTS] Crop Yield Prediction (Tonnes/Hectare):")
    print(f"   MAE:  {mae_yield:.2f} t/ha | RMSE: {rmse_yield:.2f} t/ha | R2 Score: {r2_yield:.4f}")
    print(f"[RESULTS] Market Demand Index (0-100):")
    print(f"   MAE:  {mae_dem:.2f} pts  | RMSE: {rmse_dem:.2f} pts  | R2 Score: {r2_dem:.4f}")
    print(f"[RESULTS] Mandi Price Prediction (Rs/kg):")
    print(f"   MAE:  Rs {mae_price:.2f}/kg | RMSE: Rs {rmse_price:.2f}/kg | R2 Score: {r2_price:.4f}")

    # 6. Save Model & Metadata
    model_save_path = os.path.join(models_dir, "agriwise_deepnet.pth")
    torch.save(model.state_dict(), model_save_path)
    print(f"\nModel weights saved to: {model_save_path}")

    # Build State-to-District mapping from Kaggle dataset
    state_district_map = {}
    for state, group in df.groupby("State"):
        state_district_map[state] = sorted(group["District"].unique().tolist())

    metadata = {
        "dataset_source": "Kaggle: arjunyadav99/indian-agriculture-crop-production-and-yield",
        "cat_cols": cat_cols,
        "cont_cols": cont_cols,
        "emb_dims": emb_dims,
        "categories": {col: list(label_encoders[col].classes_) for col in cat_cols},
        "districts_by_state": state_district_map,
        "scaler_mean": list(scaler.mean_),
        "scaler_scale": list(scaler.scale_),
        "test_metrics": {
            "yield": {"mae": round(float(mae_yield), 2), "rmse": round(float(rmse_yield), 2), "r2": round(float(r2_yield), 4)},
            "demand": {"mae": round(float(mae_dem), 2), "rmse": round(float(rmse_dem), 2), "r2": round(float(r2_dem), 4)},
            "price": {"mae": round(float(mae_price), 2), "rmse": round(float(rmse_price), 2), "r2": round(float(r2_price), 4)},
        }
    }

    metadata_path = os.path.join(models_dir, "model_metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"Inference metadata saved to: {metadata_path}")

    return metadata

if __name__ == "__main__":
    train_kaggle_model()
