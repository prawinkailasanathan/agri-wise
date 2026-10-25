"""
AgriWise - Inference Engine for DeepAgNet (Kaggle Dataset)
Runs multi-task predictions for crop yield, production, market demand, and mandi price by location.
"""

import json
import os
import torch
import numpy as np

from model import DeepAgNet

class AgriWisePredictor:
    def __init__(self, models_dir=None):
        if models_dir is None:
            models_dir = os.path.join(os.path.dirname(__file__), "models")
            
        self.metadata_path = os.path.join(models_dir, "model_metadata.json")
        self.weights_path = os.path.join(models_dir, "agriwise_deepnet.pth")
        
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)
            
        self.cat_cols = self.metadata["cat_cols"]
        self.cont_cols = self.metadata["cont_cols"]
        self.categories = self.metadata["categories"]
        self.scaler_mean = np.array(self.metadata["scaler_mean"])
        self.scaler_scale = np.array(self.metadata["scaler_scale"])
        emb_dims = [tuple(item) for item in self.metadata["emb_dims"]]
        
        self.model = DeepAgNet(
            emb_dims=emb_dims,
            num_cont_features=len(self.cont_cols),
            hidden_dims=[256, 128, 64],
            dropout_rate=0.0 # Inference mode
        )
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.load_state_dict(torch.load(self.weights_path, map_location=self.device))
        self.model.to(self.device)
        self.model.eval()

    def predict(self, state: str, district: str, crop: str, season: str, area_ha: float, year: int = 2024):
        """
        Runs deep learning inference based on real Kaggle agricultural dataset patterns.
        """
        # Encode categorical variables with graceful fallback for unseen labels
        cat_indices = []
        input_cats = {
            "State": state.strip().title(),
            "District": district.strip().title(),
            "Crop_Name": crop.strip().title(),
            "Season": season.strip(),
        }
        
        for col in self.cat_cols:
            val = input_cats.get(col, "")
            classes = self.categories[col]
            idx = classes.index(val) if val in classes else 0
            cat_indices.append(idx)
            
        x_cat = torch.tensor([cat_indices], dtype=torch.long).to(self.device)
        
        # Standardize continuous variables (Area_Hectares, Year)
        raw_cont = np.array([[area_ha, float(year)]], dtype=np.float32)
        scaled_cont = (raw_cont - self.scaler_mean) / self.scaler_scale
        x_cont = torch.tensor(scaled_cont, dtype=torch.float32).to(self.device)
        
        with torch.no_grad():
            p_yield, p_dem, p_price = self.model(x_cat, x_cont)
            pred_yield = float(p_yield.cpu().item())
            pred_demand = float(p_dem.cpu().item())
            pred_price = float(p_price.cpu().item())
            
        # Post-process predictions
        pred_yield = max(1.2, round(pred_yield, 2)) # Tonnes per hectare
        pred_prod = max(0.1, round(pred_yield * area_ha, 2)) # Total harvest in tonnes
        pred_demand = round(min(100.0, max(0.0, pred_demand)), 1)
        pred_price = round(max(8.0, pred_price), 2)
        
        yield_kg_per_ha = round(pred_yield * 1000, 1)
        yield_kg_per_acre = round(yield_kg_per_ha * 0.404686, 1)
        gross_value = round(pred_prod * 1000 * pred_price)

        # Categorize demand level
        if pred_demand >= 65:
            demand_level = "High Demand"
            demand_badge = "🔥 High Demand"
            demand_advice = f"Strong buyer demand for {crop} in {district} ({state}). Favorable selling conditions with low market resistance."
        elif pred_demand >= 45:
            demand_level = "Moderate Demand"
            demand_badge = "⚖️ Moderate Demand"
            demand_advice = f"Market demand for {crop} in {district} is balanced. Standard daily mandi arrivals expected."
        else:
            demand_level = "Oversupplied"
            demand_badge = "⚠️ Oversupplied Market"
            demand_advice = f"Higher regional arrivals in {district} may suppress spot prices. Consider group selling or short-term cold/crate storage."

        if pred_demand >= 65:
            rec = f"Direct delivery to District Mandi or Online channels recommended to capture high prices (~₹{pred_price}/kg)."
        elif pred_demand < 45:
            rec = f"Spot mandi rates (~₹{pred_price}/kg) reflect a seasonal supply peak. Pool transport with 4–5 farmers to cut freight by 75%."
        else:
            rec = f"Market equilibrium expected. Projected gross earnings: ₹{gross_value:,} for {pred_prod} tonnes."

        return {
            "inputs": {
                "state": state,
                "district": district,
                "crop": crop,
                "season": season,
                "area_hectares": area_ha,
                "year": year
            },
            "predictions": {
                "yield_tonnes_per_ha": pred_yield,
                "production_tonnes": pred_prod,
                "yield_kg_per_ha": yield_kg_per_ha,
                "yield_kg_per_acre": yield_kg_per_acre,
                "demand_index": pred_demand,
                "demand_level": demand_level,
                "demand_badge": demand_badge,
                "predicted_mandi_price_rs_kg": pred_price,
                "projected_gross_value_rs": gross_value,
            },
            "recommendation": rec,
            "demand_advice": demand_advice,
        }

if __name__ == "__main__":
    predictor = AgriWisePredictor()
    sample = predictor.predict(
        state="Maharashtra",
        district="Nashik",
        crop="Onion",
        season="Rabi",
        area_ha=2.5
    )
    print("\nInference Output for Nashik Onion (Kaggle Dataset Trained):")
    print(json.dumps(sample, indent=2))
