import pandas as pd
import numpy as np

def generate_messy_data(input_path="dataset/improved_tourism_dataset.csv", output_path="dataset/raw_tourism_dataset.csv"):
    print("Loading clean dataset to inject realistic noise...")
    df = pd.read_csv(input_path, low_memory=False)
    
    np.random.seed(42) # For reproducibility
    total_rows = len(df)
    
    # 1. Inject missing values (NaNs) into Rating and Ticket Price (approx 3% of data)
    rating_missing_idx = np.random.choice(df.index, size=int(total_rows * 0.03), replace=False)
    df.loc[rating_missing_idx, 'Google_Rating'] = np.nan
    
    price_missing_idx = np.random.choice(df.index, size=int(total_rows * 0.02), replace=False)
    df.loc[price_missing_idx, 'Ticket_Price'] = np.nan

    # 2. Inject extreme visitor outliers (approx 1% of data)
    # Simulating data entry errors or unchecked capacity
    outlier_idx = np.random.choice(df.index, size=int(total_rows * 0.01), replace=False)
    df.loc[outlier_idx, 'Visitors_Count'] = (df.loc[outlier_idx, 'Visitors_Count'] * np.random.uniform(10, 50, size=len(outlier_idx))).astype(int)
    
    # Also corrupt revenue for those outliers to make it unrealistic
    df.loc[outlier_idx, 'Revenue'] = df.loc[outlier_idx, 'Visitors_Count'] * 5000 

    # 3. Inject typo and formatting inconsistencies in Categorical data (approx 2% of data)
    typo_idx = np.random.choice(df.index, size=int(total_rows * 0.02), replace=False)
    
    def mess_string(s):
        if not isinstance(s, str): return s
        rand_val = np.random.random()
        if rand_val < 0.33:
            return s.lower() + "  " # Trailing whitespace and lowercase
        elif rand_val < 0.66:
            return " " + s.upper() # Leading whitespace and uppercase
        else:
            return s.replace("a", "A").replace("e", "E") # Mixed case
            
    df.loc[typo_idx, 'Location_State'] = df.loc[typo_idx, 'Location_State'].apply(mess_string)
    df.loc[typo_idx, 'Place_Type'] = df.loc[typo_idx, 'Place_Type'].apply(mess_string)

    # 4. Save the messy dataset
    df.to_csv(output_path, index=False)
    print(f"Successfully generated RAW messy dataset at {output_path}")
    print(f"- Injected {len(rating_missing_idx)} missing ratings.")
    print(f"- Injected {len(outlier_idx)} extreme visitor outliers.")
    print(f"- Injected {len(typo_idx)} string formatting errors.")

if __name__ == "__main__":
    generate_messy_data()
