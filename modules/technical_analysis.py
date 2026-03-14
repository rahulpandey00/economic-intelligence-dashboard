"""
Technical Analysis module for Stock Market Analysis.
Provides technical indicators and Elliott Wave pattern detection.
"""

import pandas as pd
import numpy as np
from typing import Tuple, List, Optional, Dict


def calculate_sma(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Simple Moving Average.
    
    Args:
        data: Price series (typically Close prices)
        period: Number of periods for the moving average
        
    Returns:
        Series with SMA values
    """
    return data.rolling(window=period).mean()


def calculate_ema(data: pd.Series, period: int) -> pd.Series:
    """
    Calculate Exponential Moving Average.
    
    Args:
        data: Price series (typically Close prices)
        period: Number of periods for the moving average
        
    Returns:
        Series with EMA values
    """
    return data.ewm(span=period, adjust=False).mean()


def calculate_rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        data: Price series (typically Close prices)
        period: RSI period (default 14)
        
    Returns:
        Series with RSI values (0-100)
    """
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(data: pd.Series, 
                   fast_period: int = 12, 
                   slow_period: int = 26, 
                   signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Moving Average Convergence Divergence (MACD).
    
    Args:
        data: Price series (typically Close prices)
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line EMA period (default 9)
        
    Returns:
        Tuple of (MACD line, Signal line, Histogram)
    """
    ema_fast = calculate_ema(data, fast_period)
    ema_slow = calculate_ema(data, slow_period)
    
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal_period)
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram


def calculate_bollinger_bands(data: pd.Series, 
                               period: int = 20, 
                               num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Bollinger Bands.
    
    Args:
        data: Price series (typically Close prices)
        period: Moving average period (default 20)
        num_std: Number of standard deviations (default 2)
        
    Returns:
        Tuple of (Upper Band, Middle Band, Lower Band)
    """
    middle_band = calculate_sma(data, period)
    std = data.rolling(window=period).std()
    
    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)
    
    return upper_band, middle_band, lower_band


def calculate_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Calculate Average True Range (ATR).
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        period: ATR period (default 14)
        
    Returns:
        Series with ATR values
    """
    prev_close = close.shift(1)
    
    tr1 = high - low
    tr2 = abs(high - prev_close)
    tr3 = abs(low - prev_close)
    
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()
    
    return atr


def calculate_stochastic(high: pd.Series, 
                         low: pd.Series, 
                         close: pd.Series, 
                         k_period: int = 14, 
                         d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate Stochastic Oscillator.
    
    Args:
        high: High price series
        low: Low price series
        close: Close price series
        k_period: %K period (default 14)
        d_period: %D smoothing period (default 3)
        
    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()
    
    k_percent = 100 * ((close - lowest_low) / (highest_high - lowest_low))
    d_percent = k_percent.rolling(window=d_period).mean()
    
    return k_percent, d_percent


def find_swing_points(data: pd.Series, window: int = 5) -> Tuple[List[int], List[int]]:
    """
    Find swing high and swing low points in price data.
    Used as a basis for Elliott Wave pattern detection.
    
    Args:
        data: Price series
        window: Window size for detecting local extrema
        
    Returns:
        Tuple of (swing_highs indices, swing_lows indices)
    """
    swing_highs = []
    swing_lows = []
    
    for i in range(window, len(data) - window):
        # Check for swing high
        if data.iloc[i] == data.iloc[i-window:i+window+1].max():
            swing_highs.append(i)
        # Check for swing low
        if data.iloc[i] == data.iloc[i-window:i+window+1].min():
            swing_lows.append(i)
    
    return swing_highs, swing_lows


def detect_elliott_waves(data: pd.Series, 
                         window: int = 10,
                         min_wave_pct: float = 0.02) -> List[Dict]:
    """
    Detect potential Elliott Wave patterns in price data.
    
    Elliott Wave Theory suggests markets move in 5 impulse waves (1-2-3-4-5)
    followed by 3 corrective waves (A-B-C).
    
    This is a simplified detection algorithm that identifies potential wave structures.
    
    Args:
        data: Price series (typically Close prices)
        window: Window for swing point detection
        min_wave_pct: Minimum wave percentage move to be considered
        
    Returns:
        List of wave points with labels
    """
    swing_highs, swing_lows = find_swing_points(data, window)
    
    # Combine and sort all swing points
    all_swings = []
    for idx in swing_highs:
        all_swings.append({'index': idx, 'price': data.iloc[idx], 'type': 'high'})
    for idx in swing_lows:
        all_swings.append({'index': idx, 'price': data.iloc[idx], 'type': 'low'})
    
    all_swings.sort(key=lambda x: x['index'])
    
    if len(all_swings) < 5:
        return []
    
    # Filter significant swings based on minimum wave percentage
    filtered_swings = [all_swings[0]]
    for swing in all_swings[1:]:
        prev_swing = filtered_swings[-1]
        pct_change = abs(swing['price'] - prev_swing['price']) / prev_swing['price']
        
        if pct_change >= min_wave_pct and swing['type'] != prev_swing['type']:
            filtered_swings.append(swing)
    
    # Label waves using Elliott Wave convention
    wave_labels = []
    impulse_labels = ['1', '2', '3', '4', '5']
    corrective_labels = ['A', 'B', 'C']
    
    # Need at least 2 swings to form a wave pattern
    if len(filtered_swings) < 2:
        return []
    
    label_idx = 0
    in_impulse = True
    
    for i, swing in enumerate(filtered_swings):
        if in_impulse:
            if label_idx < len(impulse_labels):
                wave_labels.append({
                    'index': swing['index'],
                    'price': swing['price'],
                    'label': impulse_labels[label_idx],
                    'type': swing['type'],
                    'wave_type': 'impulse'
                })
                label_idx += 1
            else:
                in_impulse = False
                label_idx = 0
        
        if not in_impulse:
            if label_idx < len(corrective_labels):
                wave_labels.append({
                    'index': swing['index'],
                    'price': swing['price'],
                    'label': corrective_labels[label_idx],
                    'type': swing['type'],
                    'wave_type': 'corrective'
                })
                label_idx += 1
    
    return wave_labels


def validate_elliott_impulse(waves: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate Elliott Wave impulse wave rules.
    
    Rules:
    1. Wave 2 cannot retrace more than 100% of Wave 1
    2. Wave 3 cannot be the shortest impulse wave
    3. Wave 4 cannot overlap with Wave 1 price territory
    
    Args:
        waves: List of wave points from detect_elliott_waves
        
    Returns:
        Tuple of (is_valid, list of violations)
    """
    violations = []
    
    impulse_waves = [w for w in waves if w.get('wave_type') == 'impulse']
    
    if len(impulse_waves) < 5:
        return False, ["Insufficient waves for validation"]
    
    # Get wave lengths
    wave_1_length = abs(impulse_waves[1]['price'] - impulse_waves[0]['price'])
    wave_2_length = abs(impulse_waves[2]['price'] - impulse_waves[1]['price'])
    wave_3_length = abs(impulse_waves[3]['price'] - impulse_waves[2]['price'])
    wave_5_length = abs(impulse_waves[4]['price'] - impulse_waves[3]['price'])
    
    # Rule 1: Wave 2 cannot retrace more than 100% of Wave 1
    if wave_2_length > wave_1_length:
        violations.append("Wave 2 retraces more than 100% of Wave 1")
    
    # Rule 2: Wave 3 cannot be the shortest impulse wave
    if wave_3_length < wave_1_length and wave_3_length < wave_5_length:
        violations.append("Wave 3 is the shortest impulse wave")
    
    # Rule 3: Wave 4 cannot overlap Wave 1 territory
    wave_1_end = impulse_waves[1]['price']
    wave_4_price = impulse_waves[4]['price']
    
    # For uptrend: wave 4 low should not go below wave 1 high
    if impulse_waves[1]['type'] == 'high':
        if wave_4_price < wave_1_end:
            violations.append("Wave 4 overlaps Wave 1 territory")
    
    is_valid = len(violations) == 0
    return is_valid, violations


def get_fibonacci_retracements(high: float, low: float) -> Dict[str, float]:
    """
    Calculate Fibonacci retracement levels.
    
    Common retracement levels used in Elliott Wave analysis.
    
    Args:
        high: Swing high price
        low: Swing low price
        
    Returns:
        Dictionary of Fibonacci levels and their prices
    """
    diff = high - low
    
    levels = {
        '0.0%': high,
        '23.6%': high - (diff * 0.236),
        '38.2%': high - (diff * 0.382),
        '50.0%': high - (diff * 0.500),
        '61.8%': high - (diff * 0.618),
        '78.6%': high - (diff * 0.786),
        '100.0%': low
    }
    
    return levels


def get_fibonacci_extensions(wave_1_start: float, 
                             wave_1_end: float, 
                             wave_2_end: float) -> Dict[str, float]:
    """
    Calculate Fibonacci extension levels.
    
    Used to project potential targets for Wave 3, 5, or C.
    
    Args:
        wave_1_start: Start price of Wave 1
        wave_1_end: End price of Wave 1
        wave_2_end: End price of Wave 2
        
    Returns:
        Dictionary of Fibonacci extension levels and their prices
    """
    wave_1_length = abs(wave_1_end - wave_1_start)
    is_uptrend = wave_1_end > wave_1_start
    
    if is_uptrend:
        levels = {
            '100%': wave_2_end + wave_1_length,
            '127.2%': wave_2_end + (wave_1_length * 1.272),
            '161.8%': wave_2_end + (wave_1_length * 1.618),
            '200%': wave_2_end + (wave_1_length * 2.0),
            '261.8%': wave_2_end + (wave_1_length * 2.618)
        }
    else:
        levels = {
            '100%': wave_2_end - wave_1_length,
            '127.2%': wave_2_end - (wave_1_length * 1.272),
            '161.8%': wave_2_end - (wave_1_length * 1.618),
            '200%': wave_2_end - (wave_1_length * 2.0),
            '261.8%': wave_2_end - (wave_1_length * 2.618)
        }
    
    return levels


def calculate_volume_profile(price: pd.Series, 
                             volume: pd.Series, 
                             num_bins: int = 20) -> pd.DataFrame:
    """
    Calculate volume profile (Volume at Price).
    
    Args:
        price: Price series
        volume: Volume series
        num_bins: Number of price bins
        
    Returns:
        DataFrame with price levels and corresponding volumes
    """
    price_range = price.max() - price.min()
    bin_size = price_range / num_bins
    
    bins = []
    volumes = []
    
    for i in range(num_bins):
        bin_low = price.min() + (i * bin_size)
        bin_high = price.min() + ((i + 1) * bin_size)
        bin_mid = (bin_low + bin_high) / 2
        
        mask = (price >= bin_low) & (price < bin_high)
        bin_volume = volume[mask].sum()
        
        bins.append(bin_mid)
        volumes.append(bin_volume)
    
    return pd.DataFrame({
        'Price': bins,
        'Volume': volumes
    })


def identify_support_resistance(data: pd.Series, 
                                window: int = 20, 
                                num_levels: int = 5) -> Tuple[List[float], List[float]]:
    """
    Identify potential support and resistance levels.
    
    Args:
        data: Price series
        window: Window for detecting swing points
        num_levels: Maximum number of levels to return
        
    Returns:
        Tuple of (support levels, resistance levels)
    """
    swing_highs, swing_lows = find_swing_points(data, window)
    
    # Get resistance levels from swing highs
    resistance_prices = [data.iloc[idx] for idx in swing_highs]
    resistance_prices.sort(reverse=True)
    resistance_levels = resistance_prices[:num_levels]
    
    # Get support levels from swing lows
    support_prices = [data.iloc[idx] for idx in swing_lows]
    support_prices.sort()
    support_levels = support_prices[:num_levels]
    
    return support_levels, resistance_levels


def get_trend_strength(data: pd.Series, period: int = 14) -> str:
    """
    Determine trend strength using ADX-like calculation.
    
    Args:
        data: Price series
        period: Period for calculation
        
    Returns:
        Trend strength description
    """
    # Simplified trend strength using price momentum
    returns = data.pct_change()
    avg_return = returns.rolling(window=period).mean().iloc[-1]
    volatility = returns.rolling(window=period).std().iloc[-1]
    
    if volatility == 0:
        return "No Trend"
    
    trend_ratio = abs(avg_return) / volatility
    
    if trend_ratio > 0.3:
        direction = "Bullish" if avg_return > 0 else "Bearish"
        return f"Strong {direction}"
    elif trend_ratio > 0.15:
        direction = "Bullish" if avg_return > 0 else "Bearish"
        return f"Moderate {direction}"
    else:
        return "Weak/Sideways"
