"""
Tourism AI: Official Data Cleaning Pipeline
-------------------------------------------
This script demonstrates an enterprise-grade data engineering pipeline.
It takes the raw, messy dataset (which contains NaNs, extreme outliers, 
and string formatting errors) and cleans it for production Machine Learning use.
"""

import pandas as pd
import numpy as np

def clean_data(input_path="dataset/raw_tourism_dataset.csv", output_path="dataset/improved_tourism_dataset.csv"):
    print(f"Loading raw messy dataset from {input_path}...")
    df = pd.read_csv(input_path, low_memory=False)
    
    initial_rows = len(df)
    
    # ── 1. Text Standardization (Fixing typos and casing) ───────────────
    print("Standardizing categorical text formats...")
    cat_cols = ['Location_State', 'Place_Type', 'Place_Name', 'Season', 'Weather_Type', 'Tourist_Type']
    for col in cat_cols:
        if col in df.columns:
            # Strip trailing/leading whitespaces and convert to Title Case
            df[col] = df[col].astype(str).str.strip().str.title()
            # Replace common typos
            df[col] = df[col].replace({"Maharastra": "Maharashtra"})
            
    # ── 2. Missing Value Imputation (Handling NaNs) ─────────────────────
    print("Imputing missing values for robust ML inference...")
    
    # Fill missing Google Ratings with the median rating of that Place_Type
    if 'Google_Rating' in df.columns:
        df['Google_Rating'] = df['Google_Rating'].fillna(
            df.groupby('Place_Type')['Google_Rating'].transform('median')
        )
        # Fallback for any remaining NaNs
        df['Google_Rating'] = df['Google_Rating'].fillna(df['Google_Rating'].median())
        
    # Fill missing Ticket Price with 0 (assuming free entry if not listed)
    if 'Ticket_Price' in df.columns:
        df['Ticket_Price'] = df['Ticket_Price'].fillna(0).astype(int)
        
    # ── 3. Advanced Outlier Capping (Enforcing Capacity Physics) ────────
    print("Applying quantile outlier capping on visitor counts and revenue...")
    
    if "Revenue" in df.columns and len(df) > 1000:
        rev_cap = int(df["Revenue"].quantile(0.995))
        df.loc[df["Revenue"] > rev_cap, "Revenue"] = rev_cap
        
    if "Visitors_Count" in df.columns and len(df) > 1000:
        vis_cap = int(df["Visitors_Count"].quantile(0.995))
        df.loc[df["Visitors_Count"] > vis_cap, "Visitors_Count"] = vis_cap

    # ── 4. Cross-Column Validation (Checking Revenue/Visitor logic) ─────
    print("Validating Revenue-to-Visitor ratios...")
    if all(c in df.columns for c in ["Revenue", "Visitors_Count", "Ticket_Price"]):
        safe_vis = df["Visitors_Count"].clip(lower=1)
        rpv = df["Revenue"] / safe_vis
        
        # Flag unrealistic per-visitor spend (e.g., > ₹5000 or < ₹5)
        unrealistic = (rpv > 5000) | (rpv < 5)
        if unrealistic.sum() > 0:
            print(f"-> Fixing {unrealistic.sum()} rows with physically impossible revenue metrics.")
            # Re-calculate revenue with a realistic multiplier
            df.loc[unrealistic, "Revenue"] = (
                df.loc[unrealistic, "Visitors_Count"] * 100
            ).astype(int)

    # ── 5. Duplicate Removal ────────────────────────────────────────────
    df.drop_duplicates(inplace=True)
    
    # Save the cleaned dataset for ML ingestion
    df.to_csv(output_path, index=False)
    
    print("\nSUCCESS: DATA CLEANING COMPLETE!")
    print(f"Processed {initial_rows} rows.")
    print(f"Clean, ML-ready dataset saved to: {output_path}")

if __name__ == "__main__":
    clean_data()
