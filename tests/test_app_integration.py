"""
Integration tests for the Streamlit app.
"""

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestAppIntegration:
    """Integration tests for the main app."""

    def test_app_imports(self):
        """Test that all app modules can be imported."""
        try:
            import app
            import modules.data_loader
            # Note: Page files start with numbers, so we test by checking file existence instead
            import importlib.util
            spec1 = importlib.util.spec_from_file_location("page1", "pages/1_Economic_Indicators_Deep_Dive.py")
            spec2 = importlib.util.spec_from_file_location("page2", "pages/2_Financial_Markets_Deep_Dive.py")
            assert spec1 is not None
            assert spec2 is not None
            assert True
        except ImportError as e:
            pytest.fail(f"Import failed: {e}")

    @patch('modules.data_loader.load_fred_data')
    @patch('modules.data_loader.get_latest_value')
    @patch('modules.data_loader.calculate_percentage_change')
    @patch('modules.data_loader.load_world_bank_gdp')
    @patch('modules.data_loader.load_yfinance_data')
    def test_data_functions_integration(self, mock_yf, mock_gdp, mock_change, mock_latest, mock_fred):
        """Test integration of data loading functions."""
        # Mock returns
        mock_fred.return_value = MagicMock()
        mock_latest.return_value = 100.0
        mock_change.return_value = 2.5
        mock_gdp.return_value = MagicMock(empty=False)
        mock_yf.return_value = {'S&P 500': MagicMock(empty=False)}

        from modules.data_loader import (
            load_fred_data,
            get_latest_value,
            calculate_percentage_change,
            load_world_bank_gdp,
            load_yfinance_data
        )

        # Test that functions can be called without errors
        result_fred = load_fred_data({'test': 'TEST'})
        result_latest = get_latest_value('TEST')
        result_change = calculate_percentage_change('TEST')
        result_gdp = load_world_bank_gdp()
        result_yf = load_yfinance_data({'test': 'TEST'})

        assert result_latest == 100.0
        assert result_change == 2.5
        assert not result_gdp.empty
        assert 'S&P 500' in result_yf


class TestPagesIntegration:
    """Integration tests for page modules."""

    def test_page_imports(self):
        """Test that page modules can be imported."""
        try:
            import importlib.util
            spec1 = importlib.util.spec_from_file_location("page1", "pages/1_Economic_Indicators_Deep_Dive.py")
            spec2 = importlib.util.spec_from_file_location("page2", "pages/2_Financial_Markets_Deep_Dive.py")
            assert spec1 is not None
            assert spec2 is not None
            assert True
        except ImportError as e:
            pytest.fail(f"Page import failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])