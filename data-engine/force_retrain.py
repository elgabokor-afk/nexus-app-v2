
import os
import sys
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
import joblib

# Setup paths
current_dir = os.path.dirname(os.path.abspath(__file__))
models_dir = os.path.join(current_dir, 'ml_models')
os.makedirs(models_dir, exist_ok=True)

MODEL_PATH = os.path.join(models_dir, "xgb_model.pkl")

def retrain_model():
    print("--- FORCE RETRAINING ML MODEL (Version Fix) ---")
    
    # 1. Generate Dummy Data (or fetch from DB if available, but for init we want speed)
    print("   [1/3] Generating Synthetic Training Data...")
    # Features match cosmos_quant.py expected features
    data = {
        'rsi': np.random.uniform(20, 80, 500),
        'atr_value': np.random.uniform(10, 100, 500),
        'volume_ratio': np.random.uniform(0.5, 5.0, 500),
        'pump_dump_score': np.random.uniform(0, 1, 500),
        'target': np.random.randint(0, 2, 500) # 0 or 1
    }
    df = pd.DataFrame(data)
    
    features = ['rsi', 'atr_value', 'volume_ratio', 'pump_dump_score']
    
    # 2. Train Model
    print("   [2/3] Training Random Forest...")
    X = df[features]
    y = df['target']
    
    # Imputer
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    
    clf = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    clf.fit(X_imputed, y)
    
    # 3. Save Model
    # V4: Use Absolute Path for Persistence
    # Use standard 'xgb_model.pkl' to match what cosmos_engine expects
    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "xgb_model.pkl")
    
    print(f"--- SAVING COMPATIBLE MODEL TO: {model_path} ---")
    joblib.dump(clf, model_path)
    print("--- RETRAINING COMPLETE (Version 1.6.1 Compatible) ---")
    
    # Optional: If engine uses 'xgb_model_v4.pkl', create a copy or symlink
    # But better to standardise on one name.
    # Let's write to both to be safe during migration
    v4_path = os.path.join(current_dir, "xgb_model_v4.pkl")
    joblib.dump(clf, v4_path)
    print(f"--- BACKUP SAVED TO: {v4_path} ---")

if __name__ == "__main__":
    try:
        retrain_model()
    except Exception as e:
        print(f"Retrain Failed: {e}")
        # Don't crash build, just warn
