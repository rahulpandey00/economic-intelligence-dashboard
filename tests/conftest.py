"""
Pytest configuration and fixtures for testing the Economic Dashboard.
"""

import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture
def sample_fred_series():
    """Sample FRED series data for testing."""
    return {
        'GDP Growth': 'A191RL1Q225SBEA',
        'CPI': 'CPIAUCSL'
    }


@pytest.fixture
def sample_yfinance_tickers():
    """Sample Yahoo Finance tickers for testing."""
    return {
        'S&P 500': '^GSPC',
        'NASDAQ': '^IXIC'
    }