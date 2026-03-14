"""
Unit tests for data_loader module.
"""

import pytest
import pandas as pd
import streamlit as st
from unittest.mock import patch, MagicMock
from modules.data_loader import (
    load_fred_data,
    load_yfinance_data,
    get_latest_value,
    calculate_percentage_change,
    load_world_bank_gdp
)


@pytest.fixture(autouse=True)
def clear_streamlit_cache():
    """Clear Streamlit cache before each test to ensure test isolation."""
    st.cache_data.clear()
    yield
    st.cache_data.clear()


class TestDataLoader:
    """Test cases for data loading functions."""

    @patch('modules.data_loader._load_cached_data', return_value=None)
    @patch('modules.data_loader.pdr.DataReader')
    def test_load_fred_data_success(self, mock_datareader, mock_cache):
        """Test successful FRED data loading."""
        # Mock data
        mock_df = pd.DataFrame({
            'A191RL1Q225SBEA': [1.0, 2.0, 3.0]
        }, index=pd.date_range('2020-01-01', periods=3))

        mock_datareader.return_value = mock_df

        series_ids = {'GDP Growth': 'A191RL1Q225SBEA'}
        result = load_fred_data(series_ids)

        assert not result.empty
        assert 'GDP Growth' in result.columns
        mock_datareader.assert_called()

    @patch('modules.data_loader._load_cached_data', return_value=None)
    @patch('modules.data_loader.pdr.DataReader')
    def test_load_fred_data_failure(self, mock_datareader, mock_cache):
        """Test FRED data loading failure."""
        mock_datareader.side_effect = Exception("API Error")

        series_ids = {'GDP Growth': 'A191RL1Q225SBEA'}
        result = load_fred_data(series_ids)

        assert result.empty

    @patch('modules.data_loader._load_cached_data', return_value=None)
    @patch('modules.data_loader.yf.download')
    def test_load_yfinance_data_success(self, mock_download, mock_cache):
        """Test successful Yahoo Finance data loading."""
        mock_df = pd.DataFrame({
            'Close': [100.0, 101.0, 102.0]
        }, index=pd.date_range('2020-01-01', periods=3))

        mock_download.return_value = mock_df

        tickers = {'S&P 500': '^GSPC'}
        result = load_yfinance_data(tickers, period="1y")

        assert 'S&P 500' in result
        assert not result['S&P 500'].empty
        mock_download.assert_called_once_with('^GSPC', period='1y', progress=False)

    @patch('modules.data_loader._load_cached_data', return_value=None)
    @patch('modules.data_loader.yf.download')
    def test_load_yfinance_data_failure(self, mock_download, mock_cache):
        """Test Yahoo Finance data loading failure."""
        mock_download.side_effect = Exception("Download Error")

        tickers = {'S&P 500': '^GSPC'}
        result = load_yfinance_data(tickers)

        assert result == {}

    @patch('modules.data_loader._load_cached_data', return_value=None)
    @patch('modules.data_loader.pdr.DataReader')
    def test_get_latest_value_success(self, mock_datareader, mock_cache):
        """Test getting latest value successfully."""
        mock_df = pd.DataFrame({
            'CPIAUCSL': [100.0, 101.0, 102.0]
        }, index=pd.date_range('2020-01-01', periods=3))

        mock_datareader.return_value = mock_df

        result = get_latest_value('CPIAUCSL')

        assert result == 102.0

    @patch('modules.data_loader._load_cached_data', return_value=None)
    @patch('modules.data_loader.pdr.DataReader')
    def test_get_latest_value_no_data(self, mock_datareader, mock_cache):
        """Test getting latest value with no data."""
        mock_df = pd.DataFrame()

        mock_datareader.return_value = mock_df

        result = get_latest_value('INVALID')

        assert result is None

    @patch('modules.data_loader._load_cached_data', return_value=None)
    @patch('modules.data_loader.pdr.DataReader')
    def test_calculate_percentage_change_success(self, mock_datareader, mock_cache):
        """Test percentage change calculation."""
        mock_df = pd.DataFrame({
            'A191RL1Q225SBEA': [100.0, 105.0, 110.0, 108.0, 112.0]
        }, index=pd.date_range('2020-01-01', periods=5))

        mock_datareader.return_value = mock_df

        result = calculate_percentage_change('A191RL1Q225SBEA', periods=1)

        # Latest: 112.0, Previous: 108.0, Change: (112-108)/108 * 100 = 3.7
        assert abs(result - 3.7) < 0.1

    def test_load_world_bank_gdp(self):
        """Test World Bank GDP loading."""
        result = load_world_bank_gdp()

        assert not result.empty
        assert 'Country' in result.columns
        assert 'GDP Growth (%)' in result.columns
        assert 'ISO3' in result.columns
        assert len(result) > 0


if __name__ == "__main__":
    pytest.main([__file__])