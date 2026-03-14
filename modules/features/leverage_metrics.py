"""
Leverage and Margin Metrics Calculator

Tracks leverage exposure indicators including short interest, margin debt,
and leveraged ETF stress signals to identify margin call risk.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import yfinance as yf
import logging

from modules.database import get_db_connection

logger = logging.getLogger(__name__)


class LeverageMetricsCalculator:
    """Calculate and store leverage and margin risk metrics."""
    
    def __init__(self):
        self.db = get_db_connection()
        
        # Leveraged ETFs to track
        self.leveraged_etfs = {
            # 3x Bull ETFs
            'TQQQ': {'name': 'ProShares UltraPro QQQ', 'leverage': 3, 'direction': 'bull', 'underlying': 'QQQ'},
            'UPRO': {'name': 'ProShares UltraPro S&P500', 'leverage': 3, 'direction': 'bull', 'underlying': 'SPY'},
            'TNA': {'name': 'Direxion Daily Small Cap Bull 3X', 'leverage': 3, 'direction': 'bull', 'underlying': 'IWM'},
            'TECL': {'name': 'Direxion Daily Technology Bull 3X', 'leverage': 3, 'direction': 'bull', 'underlying': 'XLK'},
            'FAS': {'name': 'Direxion Daily Financial Bull 3X', 'leverage': 3, 'direction': 'bull', 'underlying': 'XLF'},
            
            # 3x Bear ETFs
            'SQQQ': {'name': 'ProShares UltraPro Short QQQ', 'leverage': -3, 'direction': 'bear', 'underlying': 'QQQ'},
            'SPXU': {'name': 'ProShares UltraPro Short S&P500', 'leverage': -3, 'direction': 'bear', 'underlying': 'SPY'},
            'TZA': {'name': 'Direxion Daily Small Cap Bear 3X', 'leverage': -3, 'direction': 'bear', 'underlying': 'IWM'},
            'SOXS': {'name': 'Direxion Daily Semiconductor Bear 3X', 'leverage': -3, 'direction': 'bear', 'underlying': 'SOXX'},
            
            # 2x ETFs
            'QLD': {'name': 'ProShares Ultra QQQ', 'leverage': 2, 'direction': 'bull', 'underlying': 'QQQ'},
            'SSO': {'name': 'ProShares Ultra S&P500', 'leverage': 2, 'direction': 'bull', 'underlying': 'SPY'},
        }
    
    def fetch_short_interest(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch short interest data from Yahoo Finance.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with short interest metrics
        """
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Get current price and volume data
            hist = stock.history(period='10d')
            
            if hist.empty:
                return {}
            
            avg_volume_10d = int(hist['Volume'].mean())
            current_price = float(hist['Close'].iloc[-1])
            
            # Extract short interest metrics from info
            metrics = {
                'ticker': ticker,
                'date': datetime.now().date(),
                'short_interest': info.get('sharesShort'),
                'short_percent_float': info.get('shortPercentOfFloat'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'avg_volume_10d': avg_volume_10d,
            }
            
            # Calculate derived metrics
            if metrics['short_interest'] and avg_volume_10d > 0:
                metrics['days_to_cover'] = float(metrics['short_interest'] / avg_volume_10d)
            else:
                metrics['days_to_cover'] = None
            
            if metrics['short_interest'] and metrics['shares_outstanding']:
                metrics['short_interest_ratio'] = float(
                    metrics['short_interest'] / metrics['shares_outstanding'] * 100
                )
            else:
                metrics['short_interest_ratio'] = None
            
            logger.info(f"Fetched short interest for {ticker}: {metrics['short_percent_float']}% of float")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching short interest for {ticker}: {e}")
            return {}
    
    def fetch_finra_margin_debt(self) -> pd.DataFrame:
        """
        Fetch FINRA margin debt data from FRED.
        Series: BOGZ1FL663067003Q (Household sector; debt securities and loans; liability)
        
        Returns:
            DataFrame with margin debt time series
        """
        try:
            # Use FRED via yfinance or direct API
            # For now, return empty - will integrate with FRED data loader
            logger.warning("FINRA margin debt fetch not yet implemented - integrate with FRED loader")
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"Error fetching FINRA margin debt: {e}")
            return pd.DataFrame()
    
    def fetch_vix_term_structure(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch VIX and volatility term structure.
        
        Args:
            date: Optional date (YYYY-MM-DD)
            
        Returns:
            Dictionary with VIX metrics
        """
        try:
            # Try multiple approaches to get VIX data
            vix_close = None
            vvix_close = None
            
            # Approach 1: Try yfinance with proper error handling
            try:
                vix_data = yf.download("^VIX", period='5d', progress=False)
                if not vix_data.empty and 'Close' in vix_data.columns:
                    vix_close = float(vix_data['Close'].iloc[-1])
            except:
                pass
            
            # Approach 2: If that failed, try using FRED via data_loader
            if vix_close is None:
                try:
                    from modules.data_loader import load_fred_data
                    fred_data = load_fred_data({'VIX': 'VIXCLS'})
                    if not fred_data.empty:
                        vix_close = float(fred_data['VIX'].iloc[-1])
                except:
                    pass
            
            if vix_close is None:
                logger.warning("Could not fetch VIX data from any source")
                return {}
            
            # Estimate VVIX (historical relationship: VVIX ≈ VIX * 1.2 + 20)
            vvix_close = vix_close * 1.2 + 20
            
            # Calculate VIX regime
            vix_regime = self._classify_vix_regime(vix_close)
            
            metrics = {
                'date': date or datetime.now().date(),
                'vix': vix_close,
                'vvix': vvix_close,
                'vix_regime': vix_regime,
                'vix_3m': None,  # Would need VIX futures data
                'vix_6m': None,
                'vix_term_spread': None,
                'backwardation_ratio': None,
                'stress_score': self._calculate_vix_stress_score(vix_close, vvix_close),
            }
            
            logger.info(f"VIX: {vix_close:.2f} ({vix_regime}), Stress Score: {metrics['stress_score']:.2f}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error fetching VIX term structure: {e}")
            return {}
    
    def _classify_vix_regime(self, vix: float) -> str:
        """Classify VIX level into regime."""
        if vix < 15:
            return 'Low'
        elif vix < 20:
            return 'Normal'
        elif vix < 30:
            return 'Elevated'
        else:
            return 'Crisis'
    
    def _calculate_vix_stress_score(self, vix: float, vvix: Optional[float]) -> float:
        """
        Calculate composite VIX stress score (0-100).
        
        Components:
        - VIX level (50% weight)
        - VVIX level (50% weight)
        """
        # VIX component (normalized to 0-100)
        vix_score = min(100, (vix / 50) * 100)  # 50+ VIX = max score
        
        # VVIX component (normalized to 0-100)
        if vvix:
            vvix_score = min(100, (vvix / 150) * 100)  # 150+ VVIX = max score
        else:
            vvix_score = vix_score  # Use VIX as proxy if VVIX unavailable
        
        stress_score = (vix_score * 0.5) + (vvix_score * 0.5)
        
        return float(stress_score)
    
    def fetch_leveraged_etf_data(self, ticker: str, days: int = 30) -> pd.DataFrame:
        """
        Fetch leveraged ETF data and calculate stress indicators.
        
        Args:
            ticker: Leveraged ETF ticker
            days: Number of days of history
            
        Returns:
            DataFrame with leveraged ETF metrics
        """
        try:
            etf = yf.Ticker(ticker)
            hist = etf.history(period=f'{days}d')
            
            if hist.empty:
                return pd.DataFrame()
            
            # Calculate metrics for each day
            metrics_list = []
            
            for i in range(len(hist)):
                date = hist.index[i]
                
                # Intraday volatility (high-low range as % of close)
                intraday_vol = (hist['High'].iloc[i] - hist['Low'].iloc[i]) / hist['Close'].iloc[i] * 100
                
                # Volume ratio vs 20-day average
                if i >= 20:
                    avg_vol_20 = hist['Volume'].iloc[i-20:i].mean()
                    volume_ratio = hist['Volume'].iloc[i] / avg_vol_20 if avg_vol_20 > 0 else 1.0
                else:
                    volume_ratio = 1.0
                
                metrics = {
                    'ticker': ticker,
                    'date': date.date(),
                    'close': float(hist['Close'].iloc[i]),
                    'volume': int(hist['Volume'].iloc[i]),
                    'volume_ratio': float(volume_ratio),
                    'intraday_volatility': float(intraday_vol),
                    'tracking_error': None,  # Would need underlying comparison
                    'premium_discount': None,  # Would need NAV data
                    'stress_indicator': self._calculate_etf_stress(volume_ratio, intraday_vol),
                }
                
                metrics_list.append(metrics)
            
            df = pd.DataFrame(metrics_list)
            logger.info(f"Fetched {len(df)} days of data for {ticker}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching leveraged ETF data for {ticker}: {e}")
            return pd.DataFrame()
    
    def _calculate_etf_stress(self, volume_ratio: float, intraday_vol: float) -> float:
        """
        Calculate leveraged ETF stress indicator (0-100).
        
        Components:
        - Volume spike intensity (50%)
        - Intraday volatility (50%)
        """
        # Volume stress (>5x = max score)
        volume_stress = min(100, (volume_ratio / 5) * 100)
        
        # Volatility stress (>10% intraday = max score)
        vol_stress = min(100, (intraday_vol / 10) * 100)
        
        stress = (volume_stress * 0.5) + (vol_stress * 0.5)
        
        return float(stress)
    
    def store_leverage_metrics(self, df: pd.DataFrame) -> None:
        """Store leverage metrics in database."""
        if df.empty:
            return
        
        try:
            self.db.execute("INSERT OR REPLACE INTO leverage_metrics SELECT * FROM df")
            logger.info(f"Stored leverage metrics: {len(df)} records")
        except Exception as e:
            logger.error(f"Error storing leverage metrics: {e}")
    
    def store_vix_term_structure(self, metrics: Dict[str, Any]) -> None:
        """Store VIX term structure in database."""
        if not metrics:
            return
        
        try:
            df = pd.DataFrame([metrics])
            self.db.execute("INSERT OR REPLACE INTO vix_term_structure SELECT * FROM df")
            logger.info(f"Stored VIX term structure for {metrics['date']}")
        except Exception as e:
            logger.error(f"Error storing VIX term structure: {e}")
    
    def store_leveraged_etf_data(self, df: pd.DataFrame) -> None:
        """Store leveraged ETF data in database."""
        if df.empty:
            return
        
        try:
            self.db.execute("INSERT OR REPLACE INTO leveraged_etf_data SELECT * FROM df")
            logger.info(f"Stored leveraged ETF data: {len(df)} records")
        except Exception as e:
            logger.error(f"Error storing leveraged ETF data: {e}")
    
    def calculate_and_store_short_interest(self, ticker: str) -> Optional[pd.DataFrame]:
        """Calculate and store short interest metrics for a ticker."""
        metrics = self.fetch_short_interest(ticker)
        
        if metrics:
            df = pd.DataFrame([metrics])
            self.store_leverage_metrics(df)
            return df
        
        return None
    
    def batch_calculate_leveraged_etfs(self, days: int = 30) -> Dict[str, pd.DataFrame]:
        """Calculate metrics for all tracked leveraged ETFs."""
        results = {}
        
        for ticker, info in self.leveraged_etfs.items():
            try:
                logger.info(f"Processing leveraged ETF: {ticker} ({info['name']})")
                df = self.fetch_leveraged_etf_data(ticker, days)
                
                if not df.empty:
                    self.store_leveraged_etf_data(df)
                    results[ticker] = df
                    
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        return results
    
    def update_vix_term_structure(self) -> Optional[Dict[str, Any]]:
        """Fetch and store current VIX term structure."""
        metrics = self.fetch_vix_term_structure()
        
        if metrics:
            self.store_vix_term_structure(metrics)
            return metrics
        
        return None
