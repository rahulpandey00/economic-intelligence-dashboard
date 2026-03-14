"""
Sample World Bank GDP data for offline mode.
Contains global GDP growth data.
"""

import pandas as pd

def create_sample_world_bank_data():
    """Create sample World Bank GDP data."""
    countries_data = [
        {'Country': 'United States', 'GDP Growth (%)': 2.1, 'ISO3': 'USA'},
        {'Country': 'China', 'GDP Growth (%)': 5.2, 'ISO3': 'CHN'},
        {'Country': 'Germany', 'GDP Growth (%)': 0.9, 'ISO3': 'DEU'},
        {'Country': 'Japan', 'GDP Growth (%)': 1.0, 'ISO3': 'JPN'},
        {'Country': 'United Kingdom', 'GDP Growth (%)': 1.3, 'ISO3': 'GBR'},
        {'Country': 'France', 'GDP Growth (%)': 1.1, 'ISO3': 'FRA'},
        {'Country': 'India', 'GDP Growth (%)': 6.8, 'ISO3': 'IND'},
        {'Country': 'Brazil', 'GDP Growth (%)': 1.2, 'ISO3': 'BRA'},
        {'Country': 'Canada', 'GDP Growth (%)': 1.5, 'ISO3': 'CAN'},
        {'Country': 'South Korea', 'GDP Growth (%)': 2.6, 'ISO3': 'KOR'},
        {'Country': 'Australia', 'GDP Growth (%)': 2.3, 'ISO3': 'AUS'},
        {'Country': 'Russia', 'GDP Growth (%)': 1.8, 'ISO3': 'RUS'},
        {'Country': 'Mexico', 'GDP Growth (%)': 2.0, 'ISO3': 'MEX'},
        {'Country': 'Indonesia', 'GDP Growth (%)': 5.0, 'ISO3': 'IDN'},
        {'Country': 'Turkey', 'GDP Growth (%)': 3.5, 'ISO3': 'TUR'},
    ]

    df = pd.DataFrame(countries_data)
    return df

# Create and save sample data
if __name__ == "__main__":
    sample_df = create_sample_world_bank_data()
    sample_df.to_csv('data/sample_world_bank_gdp.csv', index=False)
    print(f"Created sample World Bank GDP data with {len(sample_df)} countries")
    print("Sample data saved to data/sample_world_bank_gdp.csv")