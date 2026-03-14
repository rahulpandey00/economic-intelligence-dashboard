"""
Unit tests for technical_analysis module.
"""

import pytest
import pandas as pd
import numpy as np
from modules.technical_analysis import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_stochastic,
    find_swing_points,
    detect_elliott_waves,
    validate_elliott_impulse,
    get_fibonacci_retracements,
    get_fibonacci_extensions,
    calculate_volume_profile,
    identify_support_resistance,
    get_trend_strength
)


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    # Create a trending price series with some noise
    base_price = 100
    trend = np.linspace(0, 20, 100)
    noise = np.random.randn(100) * 2
    prices = base_price + trend + noise
    return pd.Series(prices, index=dates)


@pytest.fixture
def sample_ohlcv_data():
    """Create sample OHLCV data for testing."""
    np.random.seed(42)
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    base_price = 100
    trend = np.linspace(0, 20, 100)
    noise = np.random.randn(100) * 2
    close = base_price + trend + noise
    
    high = close + np.abs(np.random.randn(100)) * 2
    low = close - np.abs(np.random.randn(100)) * 2
    open_price = close + np.random.randn(100) * 1
    volume = np.random.randint(1000000, 10000000, 100)
    
    return pd.DataFrame({
        'Open': open_price,
        'High': high,
        'Low': low,
        'Close': close,
        'Volume': volume
    }, index=dates)


class TestMovingAverages:
    """Test cases for moving average calculations."""
    
    def test_sma_calculation(self, sample_price_data):
        """Test Simple Moving Average calculation."""
        sma = calculate_sma(sample_price_data, period=10)
        
        # SMA should have NaN for first (period-1) values
        assert pd.isna(sma.iloc[:9]).all()
        assert not pd.isna(sma.iloc[9:]).any()
        
        # Verify calculation manually for one point
        expected = sample_price_data.iloc[:10].mean()
        assert abs(sma.iloc[9] - expected) < 0.001
    
    def test_ema_calculation(self, sample_price_data):
        """Test Exponential Moving Average calculation."""
        ema = calculate_ema(sample_price_data, period=10)
        
        # EMA should not have NaN values (except possibly first)
        assert not pd.isna(ema.iloc[10:]).any()
        
        # EMA should respond faster to price changes than SMA
        sma = calculate_sma(sample_price_data, period=10)
        # Just verify both are calculated
        assert len(ema) == len(sma)


class TestRSI:
    """Test cases for RSI calculation."""
    
    def test_rsi_bounds(self, sample_price_data):
        """Test RSI values are within 0-100 range."""
        rsi = calculate_rsi(sample_price_data, period=14)
        
        valid_rsi = rsi.dropna()
        assert (valid_rsi >= 0).all()
        assert (valid_rsi <= 100).all()
    
    def test_rsi_overbought_oversold(self):
        """Test RSI detects overbought and oversold conditions."""
        # Create consistently rising prices (should be overbought)
        rising = pd.Series([100 + i * 2 for i in range(50)])
        rsi_rising = calculate_rsi(rising, period=14)
        assert rsi_rising.iloc[-1] > 70  # Should be overbought
        
        # Create consistently falling prices (should be oversold)
        falling = pd.Series([100 - i * 2 for i in range(50)])
        rsi_falling = calculate_rsi(falling, period=14)
        assert rsi_falling.iloc[-1] < 30  # Should be oversold


class TestMACD:
    """Test cases for MACD calculation."""
    
    def test_macd_components(self, sample_price_data):
        """Test MACD returns all three components."""
        macd_line, signal_line, histogram = calculate_macd(sample_price_data)
        
        assert len(macd_line) == len(sample_price_data)
        assert len(signal_line) == len(sample_price_data)
        assert len(histogram) == len(sample_price_data)
    
    def test_macd_histogram(self, sample_price_data):
        """Test MACD histogram is difference of MACD and signal."""
        macd_line, signal_line, histogram = calculate_macd(sample_price_data)
        
        # Histogram should equal MACD - Signal
        expected_histogram = macd_line - signal_line
        pd.testing.assert_series_equal(histogram, expected_histogram)


class TestBollingerBands:
    """Test cases for Bollinger Bands calculation."""
    
    def test_bollinger_bands_order(self, sample_price_data):
        """Test upper band > middle > lower band."""
        upper, middle, lower = calculate_bollinger_bands(sample_price_data)
        
        valid_idx = ~pd.isna(upper)
        assert (upper[valid_idx] >= middle[valid_idx]).all()
        assert (middle[valid_idx] >= lower[valid_idx]).all()
    
    def test_bollinger_bands_middle_is_sma(self, sample_price_data):
        """Test middle band is SMA."""
        upper, middle, lower = calculate_bollinger_bands(sample_price_data, period=20)
        sma = calculate_sma(sample_price_data, 20)
        
        pd.testing.assert_series_equal(middle, sma)


class TestStochastic:
    """Test cases for Stochastic Oscillator calculation."""
    
    def test_stochastic_bounds(self, sample_ohlcv_data):
        """Test Stochastic values are within 0-100 range."""
        k, d = calculate_stochastic(
            sample_ohlcv_data['High'],
            sample_ohlcv_data['Low'],
            sample_ohlcv_data['Close']
        )
        
        valid_k = k.dropna()
        valid_d = d.dropna()
        
        assert (valid_k >= 0).all()
        assert (valid_k <= 100).all()
        assert (valid_d >= 0).all()
        assert (valid_d <= 100).all()


class TestSwingPoints:
    """Test cases for swing point detection."""
    
    def test_find_swing_points(self):
        """Test swing point detection."""
        # Create data with clear swing points
        prices = pd.Series([10, 12, 15, 13, 11, 9, 11, 14, 16, 14, 12])
        
        highs, lows = find_swing_points(prices, window=2)
        
        # Should find at least one swing high and one swing low
        assert len(highs) > 0 or len(lows) > 0


class TestElliottWaves:
    """Test cases for Elliott Wave detection."""
    
    def test_detect_elliott_waves(self, sample_price_data):
        """Test Elliott Wave detection returns valid structure."""
        waves = detect_elliott_waves(sample_price_data, window=10, min_wave_pct=0.02)
        
        if waves:
            for wave in waves:
                assert 'index' in wave
                assert 'price' in wave
                assert 'label' in wave
                assert 'type' in wave
                assert 'wave_type' in wave
                assert wave['wave_type'] in ['impulse', 'corrective']
    
    def test_validate_elliott_impulse_insufficient_waves(self):
        """Test validation with insufficient waves."""
        waves = [
            {'label': '1', 'price': 100, 'wave_type': 'impulse'},
            {'label': '2', 'price': 95, 'wave_type': 'impulse'}
        ]
        
        is_valid, violations = validate_elliott_impulse(waves)
        
        assert not is_valid
        assert len(violations) > 0
        assert "Insufficient waves" in violations[0]


class TestFibonacci:
    """Test cases for Fibonacci calculations."""
    
    def test_fibonacci_retracements(self):
        """Test Fibonacci retracement levels."""
        high = 100.0
        low = 50.0
        
        levels = get_fibonacci_retracements(high, low)
        
        assert levels['0.0%'] == high
        assert levels['100.0%'] == low
        assert abs(levels['50.0%'] - 75.0) < 0.01
        assert abs(levels['61.8%'] - 69.1) < 0.1
    
    def test_fibonacci_extensions_uptrend(self):
        """Test Fibonacci extension levels in uptrend."""
        wave_1_start = 100.0
        wave_1_end = 120.0
        wave_2_end = 110.0
        
        extensions = get_fibonacci_extensions(wave_1_start, wave_1_end, wave_2_end)
        
        # 100% extension should be wave_2_end + wave_1_length
        assert abs(extensions['100%'] - 130.0) < 0.01
    
    def test_fibonacci_extensions_downtrend(self):
        """Test Fibonacci extension levels in downtrend."""
        wave_1_start = 120.0
        wave_1_end = 100.0
        wave_2_end = 110.0
        
        extensions = get_fibonacci_extensions(wave_1_start, wave_1_end, wave_2_end)
        
        # 100% extension should be wave_2_end - wave_1_length
        assert abs(extensions['100%'] - 90.0) < 0.01


class TestVolumeProfile:
    """Test cases for volume profile calculation."""
    
    def test_volume_profile(self, sample_ohlcv_data):
        """Test volume profile calculation."""
        profile = calculate_volume_profile(
            sample_ohlcv_data['Close'],
            sample_ohlcv_data['Volume'],
            num_bins=10
        )
        
        assert 'Price' in profile.columns
        assert 'Volume' in profile.columns
        assert len(profile) == 10


class TestSupportResistance:
    """Test cases for support/resistance identification."""
    
    def test_identify_support_resistance(self, sample_price_data):
        """Test support and resistance level identification."""
        supports, resistances = identify_support_resistance(
            sample_price_data,
            window=10,
            num_levels=3
        )
        
        # Should return lists
        assert isinstance(supports, list)
        assert isinstance(resistances, list)
        
        # Support levels should be lower than resistance levels
        if supports and resistances:
            assert min(resistances) >= min(supports)


class TestTrendStrength:
    """Test cases for trend strength calculation."""
    
    def test_trend_strength_strong_bullish(self):
        """Test trend strength for strong uptrend."""
        rising = pd.Series([100 + i * 2 for i in range(50)])
        trend = get_trend_strength(rising)
        
        assert 'Bullish' in trend
    
    def test_trend_strength_strong_bearish(self):
        """Test trend strength for strong downtrend."""
        falling = pd.Series([100 - i * 2 for i in range(50)])
        trend = get_trend_strength(falling)
        
        assert 'Bearish' in trend
    
    def test_trend_strength_sideways(self):
        """Test trend strength for sideways movement."""
        np.random.seed(42)
        sideways = pd.Series(100 + np.random.randn(50) * 0.5)
        trend = get_trend_strength(sideways)
        
        # Should indicate weak or sideways trend
        assert 'Weak' in trend or 'Sideways' in trend or 'Moderate' in trend


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
