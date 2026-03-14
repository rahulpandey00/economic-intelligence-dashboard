"""
Sector Rotation Detector Module

Tracks sector rotation patterns using 11 S&P 500 sector ETFs:
- Relative strength vs S&P 500 benchmark
- Rotation wheel visualization
- Momentum and trend classification
- Defensive/Offensive rotation detection

Uses existing Yahoo Finance data from Market Indices page.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging

try:
    import yfinance as yf
    YF_AVAILABLE = True
except ImportError:
    YF_AVAILABLE = False

try:
    from modules.database import get_db_connection
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


class SectorRotationDetector:
    """Detect and analyze sector rotation patterns in the market."""
    
    # 11 SPDR Sector ETFs
    SECTOR_ETFS = {
        'Technology': 'XLK',
        'Healthcare': 'XLV',
        'Financials': 'XLF',
        'Consumer Discretionary': 'XLY',
        'Communication Services': 'XLC',
        'Industrials': 'XLI',
        'Consumer Staples': 'XLP',
        'Energy': 'XLE',
        'Utilities': 'XLU',
        'Real Estate': 'XLRE',
        'Materials': 'XLB'
    }
    
    # Sector classifications
    OFFENSIVE_SECTORS = ['Technology', 'Consumer Discretionary', 'Communication Services', 'Financials']
    DEFENSIVE_SECTORS = ['Utilities', 'Consumer Staples', 'Healthcare']
    CYCLICAL_SECTORS = ['Energy', 'Materials', 'Industrials', 'Real Estate']
    
    BENCHMARK = 'SPY'  # S&P 500 ETF as benchmark
    
    def __init__(self):
        if DB_AVAILABLE:
            self.db = get_db_connection()
        else:
            self.db = None
    
    def calculate_relative_strength(self, days: int = 30) -> pd.DataFrame:
        """
        Calculate relative strength of each sector vs S&P 500.
        
        Relative Strength = (Sector Return / SPY Return) - 1
        Positive RS = Outperforming
        Negative RS = Underperforming
        
        Args:
            days: Lookback period in days
            
        Returns:
            DataFrame with relative strength metrics for all sectors
        """
        if not YF_AVAILABLE:
            logger.error("yfinance not available")
            return pd.DataFrame()
        
        try:
            # Fetch benchmark data
            spy = yf.Ticker(self.BENCHMARK)
            spy_hist = spy.history(period=f'{days}d')
            
            if spy_hist.empty:
                logger.error(f"No data for benchmark {self.BENCHMARK}")
                return pd.DataFrame()
            
            spy_return = (spy_hist['Close'].iloc[-1] / spy_hist['Close'].iloc[0] - 1) * 100
            
            # Calculate relative strength for each sector
            results = []
            
            for sector, ticker in self.SECTOR_ETFS.items():
                try:
                    etf = yf.Ticker(ticker)
                    hist = etf.history(period=f'{days}d')
                    
                    if hist.empty:
                        logger.warning(f"No data for {ticker}")
                        continue
                    
                    sector_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[0] - 1) * 100
                    
                    # Relative strength (excess return over benchmark)
                    relative_strength = sector_return - spy_return
                    
                    # Calculate momentum (rate of change)
                    momentum = self._calculate_momentum(hist)
                    
                    # Classify trend
                    trend = self._classify_trend(hist)
                    
                    # Volatility
                    volatility = hist['Close'].pct_change().std() * np.sqrt(252) * 100  # Annualized
                    
                    results.append({
                        'sector': sector,
                        'ticker': ticker,
                        'sector_return': round(sector_return, 2),
                        'spy_return': round(spy_return, 2),
                        'relative_strength': round(relative_strength, 2),
                        'momentum': round(momentum, 2),
                        'trend': trend,
                        'volatility': round(volatility, 2),
                        'classification': self._classify_sector(sector),
                        'current_price': round(hist['Close'].iloc[-1], 2),
                        'volume': int(hist['Volume'].iloc[-1]),
                        'date': hist.index[-1].date()
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing {ticker}: {e}")
                    continue
            
            df = pd.DataFrame(results)
            
            if not df.empty:
                # Rank by relative strength
                df['rs_rank'] = df['relative_strength'].rank(ascending=False, method='min').astype(int)
                df = df.sort_values('relative_strength', ascending=False)
            
            return df
            
        except Exception as e:
            logger.error(f"Error calculating relative strength: {e}")
            return pd.DataFrame()
    
    def detect_rotation_pattern(self, days: int = 30) -> Dict[str, Any]:
        """
        Detect current market rotation pattern.
        
        Patterns:
        - Risk-On: Offensive sectors outperforming
        - Risk-Off: Defensive sectors outperforming
        - Cyclical Recovery: Cyclical sectors leading
        - Broadening: All sectors moving together
        - Divergence: Mixed signals
        
        Args:
            days: Lookback period
            
        Returns:
            Dictionary with rotation pattern analysis
        """
        rs_df = self.calculate_relative_strength(days)
        
        if rs_df.empty:
            return {'error': 'No data available for rotation analysis'}
        
        # Calculate average RS by sector classification
        offensive_rs = rs_df[rs_df['classification'] == 'Offensive']['relative_strength'].mean()
        defensive_rs = rs_df[rs_df['classification'] == 'Defensive']['relative_strength'].mean()
        cyclical_rs = rs_df[rs_df['classification'] == 'Cyclical']['relative_strength'].mean()
        
        # Determine rotation pattern
        pattern = self._classify_rotation(offensive_rs, defensive_rs, cyclical_rs)
        
        # Get leading and lagging sectors
        leading_sectors = rs_df.head(3)[['sector', 'relative_strength', 'ticker']].to_dict('records')
        lagging_sectors = rs_df.tail(3)[['sector', 'relative_strength', 'ticker']].to_dict('records')
        
        # Calculate sector concentration (Herfindahl index)
        rs_squared = (rs_df['relative_strength'] / rs_df['relative_strength'].sum()) ** 2
        concentration = rs_squared.sum()
        
        return {
            'pattern': pattern['name'],
            'confidence': pattern['confidence'],
            'description': pattern['description'],
            'offensive_avg_rs': round(offensive_rs, 2),
            'defensive_avg_rs': round(defensive_rs, 2),
            'cyclical_avg_rs': round(cyclical_rs, 2),
            'leading_sectors': leading_sectors,
            'lagging_sectors': lagging_sectors,
            'sector_breadth': self._calculate_breadth(rs_df),
            'concentration': round(concentration, 3),
            'lookback_days': days,
            'as_of_date': datetime.now().date().isoformat()
        }
    
    def get_rotation_wheel_data(self, days: int = 30) -> Dict[str, Any]:
        """
        Get data formatted for rotation wheel visualization.
        
        Returns position data for circular sector rotation chart.
        
        Args:
            days: Lookback period
            
        Returns:
            Dictionary with sector positions and performance
        """
        rs_df = self.calculate_relative_strength(days)
        
        if rs_df.empty:
            return {'error': 'No data available'}
        
        # Create rotation wheel positions (0-360 degrees)
        # Position based on relative strength and momentum
        wheel_data = []
        
        for _, row in rs_df.iterrows():
            # Angle based on sector (evenly distributed)
            sector_idx = list(self.SECTOR_ETFS.keys()).index(row['sector'])
            angle = (sector_idx / len(self.SECTOR_ETFS)) * 360
            
            # Radius based on relative strength (0-100 scale)
            # Normalize RS to 0-100 where 50 = neutral
            radius = 50 + (row['relative_strength'] * 2)  # Scale RS for visibility
            radius = max(0, min(100, radius))  # Clamp to 0-100
            
            wheel_data.append({
                'sector': row['sector'],
                'ticker': row['ticker'],
                'angle': angle,
                'radius': radius,
                'relative_strength': row['relative_strength'],
                'momentum': row['momentum'],
                'classification': row['classification'],
                'color': self._get_sector_color(row['classification'])
            })
        
        return {
            'sectors': wheel_data,
            'benchmark_return': round(rs_df.iloc[0]['spy_return'], 2),
            'as_of_date': datetime.now().date().isoformat()
        }
    
    def calculate_sector_correlation_matrix(self, days: int = 90) -> pd.DataFrame:
        """
        Calculate correlation matrix between all sectors.
        
        Args:
            days: Lookback period
            
        Returns:
            DataFrame correlation matrix
        """
        if not YF_AVAILABLE:
            return pd.DataFrame()
        
        try:
            # Fetch price data for all sectors
            tickers = list(self.SECTOR_ETFS.values())
            data = yf.download(tickers, period=f'{days}d', progress=False)['Close']
            
            if data.empty:
                return pd.DataFrame()
            
            # Calculate returns
            returns = data.pct_change().dropna()
            
            # Calculate correlation
            corr_matrix = returns.corr()
            
            # Rename columns/index to sector names
            ticker_to_sector = {v: k for k, v in self.SECTOR_ETFS.items()}
            corr_matrix.rename(columns=ticker_to_sector, index=ticker_to_sector, inplace=True)
            
            return corr_matrix
            
        except Exception as e:
            logger.error(f"Error calculating correlation matrix: {e}")
            return pd.DataFrame()
    
    def get_sector_momentum_scores(self, short_days: int = 10, long_days: int = 50) -> pd.DataFrame:
        """
        Calculate momentum scores using dual timeframe analysis.
        
        Args:
            short_days: Short-term momentum period
            long_days: Long-term momentum period
            
        Returns:
            DataFrame with short-term and long-term momentum
        """
        if not YF_AVAILABLE:
            return pd.DataFrame()
        
        try:
            results = []
            
            for sector, ticker in self.SECTOR_ETFS.items():
                etf = yf.Ticker(ticker)
                hist = etf.history(period=f'{long_days + 5}d')
                
                if len(hist) < long_days:
                    continue
                
                # Short-term momentum
                short_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[-short_days] - 1) * 100
                
                # Long-term momentum
                long_return = (hist['Close'].iloc[-1] / hist['Close'].iloc[-long_days] - 1) * 100
                
                # Momentum divergence
                divergence = short_return - long_return
                
                # Classify momentum
                if short_return > 0 and long_return > 0:
                    momentum_state = 'Accelerating Up'
                elif short_return > 0 and long_return < 0:
                    momentum_state = 'Reversing Up'
                elif short_return < 0 and long_return > 0:
                    momentum_state = 'Weakening'
                else:
                    momentum_state = 'Declining'
                
                results.append({
                    'sector': sector,
                    'ticker': ticker,
                    'short_term_momentum': round(short_return, 2),
                    'long_term_momentum': round(long_return, 2),
                    'divergence': round(divergence, 2),
                    'momentum_state': momentum_state,
                    'classification': self._classify_sector(sector)
                })
            
            df = pd.DataFrame(results)
            return df.sort_values('short_term_momentum', ascending=False)
            
        except Exception as e:
            logger.error(f"Error calculating momentum scores: {e}")
            return pd.DataFrame()
    
    def store_rotation_data(self, rotation_data: Dict[str, Any]) -> None:
        """Store sector rotation analysis in database."""
        if not self.db:
            return
        
        try:
            data = {
                'date': datetime.now().date(),
                'rotation_pattern': rotation_data.get('pattern'),
                'confidence': rotation_data.get('confidence'),
                'offensive_avg_rs': rotation_data.get('offensive_avg_rs'),
                'defensive_avg_rs': rotation_data.get('defensive_avg_rs'),
                'cyclical_avg_rs': rotation_data.get('cyclical_avg_rs'),
                'sector_breadth': rotation_data.get('sector_breadth'),
                'concentration': rotation_data.get('concentration'),
                'leading_sector_1': rotation_data.get('leading_sectors', [{}])[0].get('sector'),
                'leading_sector_2': rotation_data.get('leading_sectors', [{}] * 2)[1].get('sector'),
                'leading_sector_3': rotation_data.get('leading_sectors', [{}] * 3)[2].get('sector')
            }
            
            df = pd.DataFrame([data])
            self.db.insert_df(df, 'sector_rotation_analysis', if_exists='append')
            
        except Exception as e:
            logger.error(f"Error storing rotation data: {e}")
    
    # === HELPER METHODS ===
    
    def _calculate_momentum(self, hist: pd.DataFrame, period: int = 10) -> float:
        """Calculate price momentum (rate of change)."""
        if len(hist) < period:
            return 0.0
        
        return ((hist['Close'].iloc[-1] / hist['Close'].iloc[-period]) - 1) * 100
    
    def _classify_trend(self, hist: pd.DataFrame) -> str:
        """Classify trend using SMAs."""
        if len(hist) < 50:
            return 'Unknown'
        
        # Calculate SMAs
        sma_20 = hist['Close'].rolling(20).mean().iloc[-1]
        sma_50 = hist['Close'].rolling(50).mean().iloc[-1]
        current_price = hist['Close'].iloc[-1]
        
        if current_price > sma_20 > sma_50:
            return 'Strong Uptrend'
        elif current_price > sma_20:
            return 'Uptrend'
        elif current_price < sma_20 < sma_50:
            return 'Strong Downtrend'
        elif current_price < sma_20:
            return 'Downtrend'
        else:
            return 'Neutral'
    
    def _classify_sector(self, sector: str) -> str:
        """Classify sector as Offensive, Defensive, or Cyclical."""
        if sector in self.OFFENSIVE_SECTORS:
            return 'Offensive'
        elif sector in self.DEFENSIVE_SECTORS:
            return 'Defensive'
        elif sector in self.CYCLICAL_SECTORS:
            return 'Cyclical'
        return 'Other'
    
    def _classify_rotation(self, offensive_rs: float, defensive_rs: float, cyclical_rs: float) -> Dict[str, Any]:
        """Classify market rotation pattern based on sector performance."""
        
        # Risk-On: Offensive outperforming, defensive lagging
        if offensive_rs > 1 and defensive_rs < -1:
            return {
                'name': 'Risk-On',
                'confidence': 'High',
                'description': 'Investors favoring growth and cyclical sectors (bullish sentiment)'
            }
        
        # Risk-Off: Defensive outperforming, offensive lagging
        if defensive_rs > 1 and offensive_rs < -1:
            return {
                'name': 'Risk-Off',
                'confidence': 'High',
                'description': 'Flight to safety in defensive sectors (bearish sentiment)'
            }
        
        # Cyclical Recovery: Cyclical sectors leading
        if cyclical_rs > offensive_rs and cyclical_rs > defensive_rs:
            return {
                'name': 'Cyclical Recovery',
                'confidence': 'Medium',
                'description': 'Economic recovery phase with cyclical sectors leading'
            }
        
        # Broadening: All sectors positive
        if offensive_rs > 0 and defensive_rs > 0 and cyclical_rs > 0:
            return {
                'name': 'Broadening Rally',
                'confidence': 'Medium',
                'description': 'Broad-based market strength across all sectors'
            }
        
        # Divergence: Mixed signals
        return {
            'name': 'Mixed/Divergent',
            'confidence': 'Low',
            'description': 'No clear rotation pattern; mixed sector performance'
        }
    
    def _calculate_breadth(self, rs_df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate market breadth metrics."""
        total_sectors = len(rs_df)
        positive_rs = (rs_df['relative_strength'] > 0).sum()
        negative_rs = (rs_df['relative_strength'] < 0).sum()
        
        return {
            'total_sectors': total_sectors,
            'outperforming': positive_rs,
            'underperforming': negative_rs,
            'breadth_ratio': round(positive_rs / total_sectors, 2) if total_sectors > 0 else 0
        }
    
    def _get_sector_color(self, classification: str) -> str:
        """Get color code for sector classification."""
        color_map = {
            'Offensive': '#4CAF50',   # Green
            'Defensive': '#2196F3',    # Blue
            'Cyclical': '#FF9800'      # Orange
        }
        return color_map.get(classification, '#9E9E9E')
