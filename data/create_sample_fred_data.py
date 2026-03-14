"""
Sample FRED data for offline mode.
Contains historical economic indicators data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sample_fred_data():
    """Create sample FRED economic data."""
    # Create date range for last 5 years
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5)
    dates = pd.date_range(start=start_date, end=end_date, freq='Q')

    np.random.seed(42)  # For reproducible data

    # Sample economic indicators
    sample_data = {
        # GDP Growth (Quarterly %)
        'A191RL1Q225SBEA': 2.0 + np.random.normal(0, 0.5, len(dates)),

        # CPI (Consumer Price Index)
        'CPIAUCSL': 280 + np.cumsum(np.random.normal(0.8, 0.3, len(dates))),

        # Federal Funds Rate
        'FEDFUNDS': 2.5 + np.random.normal(0, 1.0, len(dates)),

        # WTI Crude Oil Price
        'DCOILWTICO': 60 + np.random.normal(0, 15, len(dates)),

        # Gold Price
        'GOLDAMGBD228NLBM': 1800 + np.random.normal(0, 200, len(dates)),

        # Euro Area GDP Growth
        'CLVMNACSCAB1GQEA19': 1.5 + np.random.normal(0, 0.8, len(dates)),

        # Euro Area Inflation
        'FPCPITOTLZGEMU': 2.0 + np.random.normal(0, 0.5, len(dates)),

        # Euro Area Unemployment
        'LRHUTTTTEZM156S': 8.0 + np.random.normal(0, 1.0, len(dates)),

        # UK GDP Growth
        'CLVMNACSCAB1GQGB': 1.2 + np.random.normal(0, 0.6, len(dates)),

        # UK Inflation
        'FPCPITOTLZGGBR': 2.5 + np.random.normal(0, 0.8, len(dates)),

        # UK Unemployment
        'LRHUTTTTGBM156S': 4.5 + np.random.normal(0, 0.8, len(dates)),

        # Japan GDP Growth
        'CLVMNACSCAB1GQJP': 0.8 + np.random.normal(0, 0.4, len(dates)),

        # Japan Inflation
        'FPCPITOTLZGJPN': 0.5 + np.random.normal(0, 0.3, len(dates)),

        # Japan Unemployment
        'LRHUTTTTJPM156S': 2.8 + np.random.normal(0, 0.5, len(dates)),

        # Canada GDP Growth
        'CLVMNACSCAB1GQCA': 2.2 + np.random.normal(0, 0.7, len(dates)),

        # Canada Inflation
        'FPCPITLZGCAN': 2.0 + np.random.normal(0, 0.6, len(dates)),

        # Canada Unemployment
        'LRHUTTTTCAM156S': 6.0 + np.random.normal(0, 1.2, len(dates)),

        # Treasury Yields
        'DGS10': 3.5 + np.random.normal(0, 0.8, len(dates)),  # 10-Year
        'DGS2': 3.0 + np.random.normal(0, 0.6, len(dates)),   # 2-Year
    }

    # Create DataFrame
    df = pd.DataFrame(sample_data, index=dates)

    # Ensure non-negative values where appropriate
    df['CPIAUCSL'] = np.maximum(df['CPIAUCSL'], 200)
    df['DCOILWTICO'] = np.maximum(df['DCOILWTICO'], 20)
    df['GOLDAMGBD228NLBM'] = np.maximum(df['GOLDAMGBD228NLBM'], 1000)

    return df

# Create and save sample data
if __name__ == "__main__":
    sample_df = create_sample_fred_data()
    sample_df.to_csv('data/sample_fred_data.csv')
    print(f"Created sample FRED data with {len(sample_df)} rows and {len(sample_df.columns)} indicators")
    print("Sample data saved to data/sample_fred_data.csv")