

import pandas as pd
import numpy as np
import streamlit as st
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import mean_absolute_error, mean_squared_error, r2_score
from utils import load_data, get_season, DESTINATION_INFO

# ─────────────────────────────────────────────────────────────────────────────
# Advanced Travel Intelligence Logic
# ─────────────────────────────────────────────────────────────────────────────

def predict_intelligence(destination: str, travel_date):
    
    if not travel_date:
        return None
        
    season = get_season(travel_date)
    info = DESTINATION_INFO.get(destination)
    
    # Base structure
    result = {
        "destination": destination,
        "month": travel_date.strftime("%B"),
        "season": season,
    }
    
    if not info:
        result.update({
            "demand": "Medium", "risk": "Medium",
            "reason": f"No specific seasonal patterns found for {destination}",
            "suggestion": f"This destination is generally good to visit! Proceed with your travel plans and enjoy exploring {destination}."
        })
        return result
        
    peak = info.get("peak", [])
    moderate = info.get("moderate", [])
    off = info.get("off", [])
    
    if season in peak:
        demand, risk = "High", "High"
        reason = f"{season} is peak season for {destination}"
        suggestion = f"⚠️ HIGH OVERCROWDING RISK! Expect large crowds and higher prices. Consider booking everything well in advance or visiting early morning."
    elif season in moderate:
        demand, risk = "Medium", "Medium"
        reason = f"{season} is a moderate/balanced season for {destination}"
        suggestion = f"Balanced trip expected. Good time to visit for a mix of experience and manageable crowds."
    else:
        demand, risk = "Low", "Low"
        reason = f"{season} is off-season for {destination} tourism"
        perks = info.get("off_perks", "low cost, less crowd")
        warn = info.get("off_warnings", "limited activities")
        suggestion = f"Good for budget travel, but {warn}"

    result.update({
        "demand": demand,
        "risk": risk,
        "reason": reason,
        "suggestion": suggestion
    })
    return result

# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers — Feature Preparation for XGBoost
# ─────────────────────────────────────────────────────────────────────────────

def _prepare_features(df: pd.DataFrame):
    """Prepare features for the XGBoost model.
    Returns (X, y_demand, feature_cols, encoders, place_means, global_mean).
    """
    d = df.copy()

    # Pre-calculate place means for relative comparison
    place_means = d.groupby("Place_Name")["Visitors_Count"].mean().to_dict()
    global_mean = d["Visitors_Count"].mean()

    # ── Categorical Encoding ─────────────────────────────────────────────
    cat_cols = ["Place_Name", "Location_State", "Place_Type", "Season", 
                "Day_of_Week", "Weather_Type", "Is_Weekend", "Tourist_Type"]
    
    encoders = {}
    for col in cat_cols:
        if col in d.columns:
            le = LabelEncoder()
            # Handle unknown values by adding a dedicated label
            unique_vals = list(d[col].astype(str).unique()) + ["Unknown"]
            le.fit(unique_vals)
            d[col] = le.transform(d[col].astype(str))
            encoders[col] = le

    # ── Numeric Features (expanded for improved dataset) ─────────────────
    num_cols = ["Google_Rating", "Ticket_Price", "Review_Count_Lakhs",
                "Hotel_Occupancy_Rate", "Month_Num", "Year",
                "Is_Event", "Has_Airport"]
    for col in num_cols:
        if col in d.columns:
            d[col] = pd.to_numeric(d[col], errors="coerce").fillna(0)

    feature_cols = cat_cols + num_cols
    feature_cols = [c for c in feature_cols if c in d.columns]

    d = d.dropna(subset=feature_cols + ["Visitors_Count"])

    X = d[feature_cols]
    y = d["Visitors_Count"]

    return X, y, feature_cols, encoders, place_means, global_mean

# ─────────────────────────────────────────────────────────────────────────────
# Model cache — XGBoost Regressor
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def train_models():
    """Train XGBoost regression model for demand forecasting.
    Cached as a resource so it persists across reruns.
    Cache busted for 36-state merged UT dataset.
    """
    df = load_data()
    if df.empty:
        return None

    X, y, feature_cols, encoders, place_means, global_mean = _prepare_features(df)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.15, random_state=42
    )

    # ── XGBoost Regressor — Production Configuration ─────────────────────
    xgb_reg = XGBRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=8,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        n_jobs=-1,
        tree_method="hist",          # fast histogram-based training
        verbosity=0,
    )
    xgb_reg.fit(X_train, y_train)
    
    y_pred = xgb_reg.predict(X_test)
    r2   = r2_score(y_test, y_pred)
    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))

    return {
        "xgb_reg":      xgb_reg,
        "encoders":     encoders,
        "feature_cols": feature_cols,
        "place_means":  place_means,
        "global_mean":  global_mean,
        "X_test":       X_test,
        "y_test":       y_test,
        "y_pred":       y_pred,
        "metrics": {
            "r2":   round(r2, 4),
            "mae":  round(mae, 2),
            "rmse": round(rmse, 2),
        }
    }

# ─────────────────────────────────────────────────────────────────────────────
# Prediction API
# ─────────────────────────────────────────────────────────────────────────────

def predict(state: str, place_type: str, season: str,
            weather: str, tourists: int, is_weekend: bool,
            ticket_price: int, rating: float, travel_date=None,
            place_name: str = "Unknown"):
    
    models = train_models()
    if models is None:
        return None

    # Precise Day name
    day_name = travel_date.strftime("%A") if travel_date else ("Saturday" if is_weekend else "Wednesday")
    
    # Month number from travel date
    month_num = travel_date.month if travel_date else 6
    year_val  = travel_date.year if travel_date else 2025
    
    # Feature Input
    raw = {
        "Place_Name":           place_name,
        "Location_State":       state,
        "Place_Type":           place_type,
        "Season":               season,
        "Day_of_Week":          day_name,
        "Weather_Type":         weather,
        "Is_Weekend":           "Yes" if is_weekend else "No",
        "Tourist_Type":         "Domestic",
        "Google_Rating":        rating,
        "Ticket_Price":         ticket_price,
        "Review_Count_Lakhs":   1.0,
        "Hotel_Occupancy_Rate": 50.0,
        "Month_Num":            month_num,
        "Year":                 year_val,
        "Is_Event":             0,
        "Has_Airport":          1,
    }

    enc = models["encoders"]
    row = {}
    for col in models["feature_cols"]:
        val = raw.get(col, "Unknown")
        if col in enc:
            if str(val) not in enc[col].classes_:
                val = "Unknown"
            val = enc[col].transform([str(val)])[0]
        row[col] = val

    X_input = pd.DataFrame([row])[models["feature_cols"]]

    # Predict Demand using XGBoost
    demand = int(models["xgb_reg"].predict(X_input)[0])
    
    # Compare with Place Mean to determine Crowd Level
    avg = models["place_means"].get(place_name, models["global_mean"])
    
    # Thresholds for relative labeling (Refined and balanced)
    # High: > 20% above average
    # Low:  < 15% below average
    if demand > 1.20 * avg:
        label = "High"
    elif demand < 0.85 * avg:
        label = "Low"
    else:
        label = "Medium"

    return {
        "demand":       demand,
        "crowd_label":  label,
        "avg_visitors": int(avg)
    }
