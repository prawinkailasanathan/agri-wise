# AgriWise 🌾

> **Smart Agricultural Assistant & Deep Learning Crop Forecasting for Indian Farmers**

AgriWise is an AI-powered agricultural web application designed to help Indian vegetable and crop farmers make data-driven planting, harvesting, and marketing decisions. It forecasts district-level yield, APMC market demand, and equilibrium selling rates using deep learning, and helps farmers maximize profit through cooperative selling and proper post-harvest storage.

---

## 🌟 Key Features

### 1. 🤖 AI Crop Production & Market Demand Predictor (Deep Learning)
* Powered by **DeepAgNet**, a multi-task tabular deep neural network with Entity Embeddings.
* Trained on **575,000+ real records** from the Kaggle dataset [`arjunyadav99/indian-agriculture-crop-production-and-yield`](https://www.kaggle.com/datasets/arjunyadav99/indian-agriculture-crop-production-and-yield) (sourced from Ministry of Agriculture & Farmers Welfare).
* **Coverage**: 32 Indian States and 621 Districts.
* **Forecasting Targets**:
  * **Crop Yield**: $\text{Tonnes/Hectare}$ and plot-level harvest volume ($\text{Tonnes}$ / $\text{kg}$).
  * **Market Demand Index**: $0\text{--}100$ score with status badges (🔥 *High Demand*, ⚖️ *Moderate Demand*, ⚠️ *Oversupplied*).
  * **Equilibrium Mandi Price**: Projected spot price ($\text{₹/kg}$) and gross revenue.
* **Interactive Bridge**: One-click transfer of forecast results directly into the Profit Calculator.

### 2. 🌿 Crop Library (18+ Crops)
Comprehensive profiles and storage parameters for staple crops: Tomato, Onion, Potato, Green Chilli, Brinjal, Lady's Finger, Cauliflower, Cabbage, Drumstick, Radish, Coriander, Mint, Beans, Carrot, Garlic, Ginger, Turmeric, Banana, etc.

### 3. 📊 Multi-Channel Market Price Comparison
Side-by-side comparison across three market levels:
* 🏪 **Local Mandi** (farmgate rate)
* 🏢 **District Market** (+25–35% higher return)
* 💻 **Online / Direct Platforms** (+45–65% premium)
* Direct reference links to [Agmarknet.gov.in](https://agmarknet.gov.in).

### 4. 🧮 Interactive Profit Calculator
Calculates real take-home net profit/loss by factoring in:
* Production costs (seeds, fertilizer, water, labor)
* Two-way vehicle transport costs ($\text{rate/km} \times \text{distance} \times 2$)
* Mandi commission fees ($2\text{--}5\%$)
* Packaging materials (crates, bags)

### 5. 🤝 Cooperative Selling & FPO Guide
Case study showing how 5 farmers pooling harvests can increase net profit by $+54\%$ through shared freight and bulk bargaining power.

### 6. 📦 Post-Harvest Storage Guidance
Storage protocols based on ICAR guidelines: temperature, relative humidity, maximum shelf-life, container formats, and critical ethylene separation rules.

---

## 🏗️ System Architecture & Tech Stack

```
Frontend (HTML5, Vanilla CSS3, JavaScript)
       │
       ▼  HTTP / REST
FastAPI Server (Port 8000)
       │
       ▼  PyTorch Inference
DeepAgNet (Multi-Task Tabular Deep Neural Network)
       │
       ▼  Entity Embeddings
Trained on 33,826 cleaned records (Kaggle / MoAFW historical census)
```

* **Frontend**: Vanilla HTML5, modern CSS3 variables, responsive layout, JavaScript.
* **Backend**: FastAPI, Uvicorn, Pydantic, Python.
* **Deep Learning**: PyTorch (`torch`), NumPy, Pandas, Scikit-Learn.
* **Data Source**: Kaggle (`arjunyadav99/indian-agriculture-crop-production-and-yield`).

---

## 🚀 Quick Start Guide

### 1. Clone the Repository
```bash
git clone https://github.com/dharshine2424-sudo/AgriWise.git
cd AgriWise
```

### 2. Setup Python Environment & Dependencies
```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate
# On Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 3. (Optional) Re-download Dataset & Train Model
```bash
# Download dataset from Kaggle
python ml/download_kaggle_dataset.py

# Preprocess & enrich with APMC market dynamics
python ml/prepare_kaggle_data.py

# Train DeepAgNet model
python ml/train.py
```
*(Pre-trained model weights are already included in `ml/models/agriwise_deepnet.pth`)*

### 4. Run the Application

**Start the Deep Learning API Backend:**
```bash
python ml/server.py
# Running on http://127.0.0.1:8000
```

**Start the Web Frontend:**
```bash
python -m http.server 3000
# Open http://127.0.0.1:3000 in your browser
```

---

## 📄 License
This project is open-source and intended for educational and agricultural empowerment purposes.