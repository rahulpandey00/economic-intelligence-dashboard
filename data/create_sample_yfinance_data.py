"""
Sample Yahoo Finance data for offline mode.
Contains historical stock market data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def create_sample_yfinance_data():
    """Create sample Yahoo Finance market data."""
    # Create date range for last 5 years (daily data)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365*5)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')

    np.random.seed(123)  # For reproducible data

    # Sample market indices
    indices = {
        '^GSPC': {'name': 'S&P 500', 'start_price': 3500, 'volatility': 0.02},  # S&P 500
        '^IXIC': {'name': 'NASDAQ', 'start_price': 12000, 'volatility': 0.025}, # NASDAQ
        '^FTSE': {'name': 'FTSE 100', 'start_price': 7500, 'volatility': 0.015}, # FTSE 100
        '^N225': {'name': 'Nikkei 225', 'start_price': 28000, 'volatility': 0.02}, # Nikkei
        '^GDAXI': {'name': 'DAX', 'start_price': 13000, 'volatility': 0.018}, # DAX
        '^HSI': {'name': 'Hang Seng', 'start_price': 25000, 'volatility': 0.022}, # Hang Seng
    }

    sample_data = {}

    for ticker, info in indices.items():
        # Generate random walk prices
        price_changes = np.random.normal(0.0005, info['volatility'], len(dates))
        prices = info['start_price'] * np.exp(np.cumsum(price_changes))

        # Create OHLC data
        high_mult = 1 + np.abs(np.random.normal(0, 0.01, len(dates)))
        low_mult = 1 - np.abs(np.random.normal(0, 0.01, len(dates)))
        open_prices = prices * (1 + np.random.normal(0, 0.005, len(dates)))
        volume = np.random.randint(1000000, 10000000, len(dates))

        df = pd.DataFrame({
            'Open': open_prices,
            'High': prices * high_mult,
            'Low': prices * low_mult,
            'Close': prices,
            'Adj Close': prices * 0.98,  # Slight adjustment for dividends
            'Volume': volume
        }, index=dates)

        sample_data[ticker] = df

    return sample_data

# Create and save sample data
if __name__ == "__main__":
    sample_data = create_sample_yfinance_data()

    for ticker, df in sample_data.items():
        filename = f"data/sample_{ticker.replace('^', '')}_data.csv"
        df.to_csv(filename)
        print(f"Created sample data for {ticker} with {len(df)} rows")

    print("All sample Yahoo Finance data saved to data/ directory")