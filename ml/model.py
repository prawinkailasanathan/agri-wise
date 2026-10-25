"""
AgriWise - Deep Learning Architecture for Crop Production & Market Demand
Multi-Task Tabular Deep Neural Network with Entity Embeddings (DeepAgNet).
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class DeepAgNet(nn.Module):
    def __init__(self, emb_dims, num_cont_features, hidden_dims=[256, 128, 64], dropout_rate=0.2):
        super(DeepAgNet, self).__init__()
        
        # Entity Embeddings for categorical features
        # emb_dims is a list of tuples: [(num_categories, emb_dim), ...]
        self.embeddings = nn.ModuleList([
            nn.Embedding(num_cat, emb_dim) for num_cat, emb_dim in emb_dims
        ])
        
        total_emb_dim = sum(emb_dim for _, emb_dim in emb_dims)
        total_in_dim = total_emb_dim + num_cont_features
        
        # Backbone Feature Extractor
        self.input_bn = nn.BatchNorm1d(num_cont_features)
        
        # Layer 1
        self.fc1 = nn.Linear(total_in_dim, hidden_dims[0])
        self.bn1 = nn.BatchNorm1d(hidden_dims[0])
        self.drop1 = nn.Dropout(dropout_rate)
        
        # Layer 2 with skip/residual capability
        self.fc2 = nn.Linear(hidden_dims[0], hidden_dims[1])
        self.bn2 = nn.BatchNorm1d(hidden_dims[1])
        self.drop2 = nn.Dropout(dropout_rate)
        
        # Layer 3
        self.fc3 = nn.Linear(hidden_dims[1], hidden_dims[2])
        self.bn3 = nn.BatchNorm1d(hidden_dims[2])
        self.drop3 = nn.Dropout(dropout_rate / 2)
        
        # --- Multi-Task Prediction Heads ---
        # Head 1: Production Head (Predicts Crop Production in Tonnes)
        self.prod_head = nn.Sequential(
            nn.Linear(hidden_dims[2], 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Softplus() # Production is strictly >= 0
        )
        
        # Head 2: Market Demand Head (Predicts Demand Index 0 - 100)
        self.demand_head = nn.Sequential(
            nn.Linear(hidden_dims[2], 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Sigmoid() # Will be multiplied by 100
        )
        
        # Head 3: Equilibrium Market Price Head (Predicts ₹ / kg)
        self.price_head = nn.Sequential(
            nn.Linear(hidden_dims[2], 32),
            nn.ReLU(),
            nn.Linear(32, 1),
            nn.Softplus() # Price is strictly >= 0
        )

    def forward(self, x_cat, x_cont):
        # Extract and concatenate entity embeddings
        emb_outputs = []
        for i, emb_layer in enumerate(self.embeddings):
            emb_outputs.append(emb_layer(x_cat[:, i]))
        x_emb = torch.cat(emb_outputs, dim=1)
        
        # Batch normalize continuous features
        x_cont_norm = self.input_bn(x_cont)
        
        # Fuse tabular representations
        x = torch.cat([x_emb, x_cont_norm], dim=1)
        
        # Deep representation learning
        x = self.drop1(F.leaky_relu(self.bn1(self.fc1(x)), negative_slope=0.1))
        x = self.drop2(F.leaky_relu(self.bn2(self.fc2(x)), negative_slope=0.1))
        x = self.drop3(F.leaky_relu(self.bn3(self.fc3(x)), negative_slope=0.1))
        
        # Multi-task predictions
        pred_prod = self.prod_head(x)
        pred_demand = self.demand_head(x) * 100.0
        pred_price = self.price_head(x)
        
        return pred_prod, pred_demand, pred_price
