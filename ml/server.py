"""
AgriWise - FastAPI Prediction Server
Provides real-time API endpoints for crop production & market demand prediction.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional
import uvicorn
import os
import json

from predict import AgriWisePredictor

app = FastAPI(
    title="AgriWise AI - Crop Production & Market Demand API",
    description="Multi-Task Deep Learning model for predicting crop yield, market demand, and equilibrium mandi prices across Indian districts.",
    version="1.0.0"
)

# Enable CORS for browser access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load predictor at startup
predictor = AgriWisePredictor()

class PredictionRequest(BaseModel):
    state: str = Field(..., example="Maharashtra")
    district: str = Field(..., example="Nashik")
    crop: str = Field(..., example="Onion")
    season: str = Field(..., example="Rabi")
    area_hectares: float = Field(..., gt=0.0, example=2.5)
    soil_type: Optional[str] = Field("Alluvial", example="Black Soil")
    rainfall_mm: Optional[float] = Field(850.0, example=850.0)
    temperature_c: Optional[float] = Field(26.0, example=26.0)
    fertilizer_kg_per_ha: Optional[float] = Field(120.0, example=120.0)
    irrigation_pct: Optional[float] = Field(75.0, example=75.0)

@app.get("/")
def home():
    return {
        "status": "online",
        "service": "AgriWise Deep Learning Inference API",
        "model": "DeepAgNet (Multi-Task Tabular DNN with Entity Embeddings)",
        "endpoints": ["/api/metadata", "/api/predict"]
    }

@app.get("/api/metadata")
def get_metadata():
    metadata = predictor.metadata
    state_district_map = metadata.get("districts_by_state", {})
    if not state_district_map:
        state_district_map = {s: ["Default"] for s in metadata["categories"]["State"]}

    return {
        "dataset_source": metadata.get("dataset_source", "Kaggle Indian Agriculture Dataset"),
        "states": sorted(list(state_district_map.keys())),
        "districts_by_state": state_district_map,
        "crops": metadata["categories"].get("Crop_Name", metadata["categories"].get("Crop", [])),
        "seasons": metadata["categories"]["Season"],
        "metrics": metadata.get("test_metrics", {})
    }

@app.post("/api/predict")
def predict_crop(req: PredictionRequest):
    try:
        result = predictor.predict(
            state=req.state,
            district=req.district,
            crop=req.crop,
            season=req.season,
            area_ha=req.area_hectares
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("Starting AgriWise AI Server on http://127.0.0.1:8000 ...")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
