"""
Margin Call Risk Composite Calculator

Combines leverage, volatility, options positioning, and liquidity metrics
to generate a composite margin call risk score for stocks.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from modules.database import get_db_connection, get_technical_features
from modules.features.options_metrics import OptionsMetricsCalculator

logger = logging.getLogger(__name__)


class MarginCallRiskCalculator:
    """Calculate composite margin call risk scores."""
    
    def __init__(self):
        self.db = get_db_connection()
        self.options_calc = OptionsMetricsCalculator()
        
        # Component weights
        self.weights = {
            'leverage': 0.30,
            'volatility': 0.25,
            'options': 0.25,
            'liquidity': 0.20,
        }
    
    def calculate_leverage_score(
        self,
        short_interest_pct: Optional[float],
        days_to_cover: Optional[float],
        short_interest_ratio: Optional[float]
    ) -> float:
        """
        Calculate leverage component score (0-100).
        
        High scores indicate:
        - High short interest (>20% of float)
        - High days to cover (>10 days)
        - Growing short positions
        """
        score = 0
        count = 0
        
        # Short interest as % of float
        if short_interest_pct is not None:
            if short_interest_pct > 30:
                si_score = 100
            elif short_interest_pct > 20:
                si_score = 75
            elif short_interest_pct > 10:
                si_score = 50
            elif short_interest_pct > 5:
                si_score = 25
            else:
                si_score = 0
            score += si_score
            count += 1
        
        # Days to cover
        if days_to_cover is not None:
            if days_to_cover > 15:
                dtc_score = 100
            elif days_to_cover > 10:
                dtc_score = 75
            elif days_to_cover > 5:
                dtc_score = 50
            elif days_to_cover > 2:
                dtc_score = 25
            else:
                dtc_score = 0
            score += dtc_score
            count += 1
        
        # Short interest ratio (% of shares outstanding)
        if short_interest_ratio is not None:
            if short_interest_ratio > 15:
                sir_score = 100
            elif short_interest_ratio > 10:
                sir_score = 75
            elif short_interest_ratio > 5:
                sir_score = 50
            else:
                sir_score = 25
            score += sir_score
            count += 1
        
        return score / count if count > 0 else 50.0  # Default to neutral
    
    def calculate_volatility_score(
        self,
        current_vol: Optional[float],
        bb_width: Optional[float],
        atr_to_price: Optional[float],
        vix: Optional[float]
    ) -> float:
        """
        Calculate volatility component score (0-100).
        
        High scores indicate:
        - High realized volatility (>40% annualized)
        - Wide Bollinger Bands (>95th percentile)
        - High VIX (>25)
        """
        score = 0
        count = 0
        
        # Realized volatility (annualized %)
        if current_vol is not None:
            if current_vol > 60:
                vol_score = 100
            elif current_vol > 40:
                vol_score = 75
            elif current_vol > 25:
                vol_score = 50
            elif current_vol > 15:
                vol_score = 25
            else:
                vol_score = 0
            score += vol_score
            count += 1
        
        # Bollinger Band width (wider = more volatile)
        if bb_width is not None:
            # Assuming bb_width is already normalized (0-1 range typically)
            bb_score = min(100, bb_width * 200)  # Scale to 0-100
            score += bb_score
            count += 1
        
        # ATR to price ratio
        if atr_to_price is not None:
            if atr_to_price > 0.05:
                atr_score = 100
            elif atr_to_price > 0.03:
                atr_score = 75
            elif atr_to_price > 0.02:
                atr_score = 50
            else:
                atr_score = 25
            score += atr_score
            count += 1
        
        # VIX level (market-wide fear gauge)
        if vix is not None:
            if vix > 35:
                vix_score = 100
            elif vix > 25:
                vix_score = 75
            elif vix > 20:
                vix_score = 50
            elif vix > 15:
                vix_score = 25
            else:
                vix_score = 0
            score += vix_score
            count += 1
        
        return score / count if count > 0 else 50.0
    
    def calculate_options_score(
        self,
        put_call_ratio: Optional[float],
        iv_rank: Optional[float],
        put_iv_mean: Optional[float],
        call_iv_mean: Optional[float]
    ) -> float:
        """
        Calculate options positioning component score (0-100).
        
        High scores indicate:
        - High put/call ratio (>1.5 = heavy put buying)
        - High IV rank (>75 = elevated volatility expectations)
        - Put skew (put IV > call IV by >20%)
        """
        score = 0
        count = 0
        
        # Put/Call ratio
        if put_call_ratio is not None:
            if put_call_ratio > 2.0:
                pcr_score = 100
            elif put_call_ratio > 1.5:
                pcr_score = 75
            elif put_call_ratio > 1.0:
                pcr_score = 50
            elif put_call_ratio > 0.7:
                pcr_score = 25
            else:
                pcr_score = 0
            score += pcr_score
            count += 1
        
        # IV Rank
        if iv_rank is not None:
            if iv_rank > 90:
                iv_score = 100
            elif iv_rank > 75:
                iv_score = 75
            elif iv_rank > 50:
                iv_score = 50
            elif iv_rank > 25:
                iv_score = 25
            else:
                iv_score = 0
            score += iv_score
            count += 1
        
        # Put skew (put IV - call IV)
        if put_iv_mean is not None and call_iv_mean is not None:
            skew = (put_iv_mean - call_iv_mean) / call_iv_mean * 100
            if skew > 30:
                skew_score = 100
            elif skew > 20:
                skew_score = 75
            elif skew > 10:
                skew_score = 50
            elif skew > 0:
                skew_score = 25
            else:
                skew_score = 0
            score += skew_score
            count += 1
        
        return score / count if count > 0 else 50.0
    
    def calculate_liquidity_score(
        self,
        volume_trend: Optional[float],
        volume_ratio: Optional[float],
        bid_ask_spread: Optional[float]
    ) -> float:
        """
        Calculate liquidity component score (0-100).
        
        High scores indicate:
        - Declining volume while volatility rising
        - Below-average volume
        - Wide bid-ask spreads
        """
        score = 0
        count = 0
        
        # Volume trend (negative = declining)
        if volume_trend is not None:
            if volume_trend < -30:
                trend_score = 100
            elif volume_trend < -15:
                trend_score = 75
            elif volume_trend < 0:
                trend_score = 50
            elif volume_trend < 15:
                trend_score = 25
            else:
                trend_score = 0
            score += trend_score
            count += 1
        
        # Volume ratio vs average
        if volume_ratio is not None:
            if volume_ratio < 0.5:
                vr_score = 100
            elif volume_ratio < 0.7:
                vr_score = 75
            elif volume_ratio < 0.9:
                vr_score = 50
            elif volume_ratio < 1.1:
                vr_score = 25
            else:
                vr_score = 0
            score += vr_score
            count += 1
        
        # Bid-ask spread (if available)
        if bid_ask_spread is not None:
            if bid_ask_spread > 0.02:
                spread_score = 100
            elif bid_ask_spread > 0.01:
                spread_score = 75
            elif bid_ask_spread > 0.005:
                spread_score = 50
            else:
                spread_score = 25
            score += spread_score
            count += 1
        
        return score / count if count > 0 else 50.0
    
    def calculate_composite_risk(
        self,
        ticker: str,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculate composite margin call risk score for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            date: Optional date (YYYY-MM-DD), defaults to latest
            
        Returns:
            Dictionary with all risk components and composite score
        """
        try:
            # Get leverage metrics
            leverage_query = """
                SELECT * FROM leverage_metrics
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT 1
            """
            leverage_df = self.db.query(leverage_query, (ticker,))
            
            # Get technical features (for volatility and volume)
            tech_features = get_technical_features(ticker)
            
            # Get options data
            options_query = """
                SELECT * FROM options_data
                WHERE ticker = ?
                ORDER BY date DESC
                LIMIT 1
            """
            options_df = self.db.query(options_query, (ticker,))
            
            # Get VIX data
            vix_query = """
                SELECT * FROM vix_term_structure
                ORDER BY date DESC
                LIMIT 1
            """
            vix_df = self.db.query(vix_query)
            
            # Extract metrics with None defaults
            leverage_data = leverage_df.iloc[0] if not leverage_df.empty else None
            tech_data = tech_features.iloc[-1] if not tech_features.empty else None
            options_data = options_df.iloc[0] if not options_df.empty else None
            vix_data = vix_df.iloc[0] if not vix_df.empty else None
            
            # Calculate component scores
            leverage_score = self.calculate_leverage_score(
                leverage_data['short_percent_float'] if leverage_data is not None else None,
                leverage_data['days_to_cover'] if leverage_data is not None else None,
                leverage_data['short_interest_ratio'] if leverage_data is not None else None
            )
            
            volatility_score = self.calculate_volatility_score(
                tech_data['hist_vol_20'] if tech_data is not None and 'hist_vol_20' in tech_data else None,
                tech_data['bb_width'] if tech_data is not None and 'bb_width' in tech_data else None,
                tech_data['atr_14'] / tech_data['close'] if tech_data is not None and 'atr_14' in tech_data else None,
                vix_data['vix'] if vix_data is not None else None
            )
            
            options_score = self.calculate_options_score(
                options_data['put_call_volume_ratio'] if options_data is not None else None,
                options_data['iv_rank'] if options_data is not None else None,
                options_data['total_put_iv'] if options_data is not None else None,
                options_data['total_call_iv'] if options_data is not None else None
            )
            
            liquidity_score = self.calculate_liquidity_score(
                None,  # Would need historical volume comparison
                tech_data['volume_ratio'] if tech_data is not None and 'volume_ratio' in tech_data else None,
                None  # Bid-ask spread not readily available
            )
            
            # Calculate composite score
            composite_score = (
                leverage_score * self.weights['leverage'] +
                volatility_score * self.weights['volatility'] +
                options_score * self.weights['options'] +
                liquidity_score * self.weights['liquidity']
            )
            
            # Classify risk level
            if composite_score >= 75:
                risk_level = 'Critical'
            elif composite_score >= 60:
                risk_level = 'High'
            elif composite_score >= 40:
                risk_level = 'Moderate'
            elif composite_score >= 25:
                risk_level = 'Low'
            else:
                risk_level = 'Minimal'
            
            result = {
                'ticker': ticker,
                'date': date or datetime.now().date(),
                'leverage_score': float(leverage_score),
                'volatility_score': float(volatility_score),
                'options_score': float(options_score),
                'liquidity_score': float(liquidity_score),
                'composite_risk_score': float(composite_score),
                'risk_level': risk_level,
                'vix_regime': vix_data['vix_regime'] if vix_data is not None else 'Unknown',
                'short_interest_pct': float(leverage_data['short_percent_float']) if leverage_data is not None and leverage_data['short_percent_float'] is not None else None,
                'put_call_ratio': float(options_data['put_call_volume_ratio']) if options_data is not None and options_data['put_call_volume_ratio'] is not None else None,
                'iv_rank': float(options_data['iv_rank']) if options_data is not None and options_data['iv_rank'] is not None else None,
            }
            
            logger.info(f"{ticker} margin call risk: {composite_score:.1f} ({risk_level})")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating margin call risk for {ticker}: {e}")
            return {}
    
    def store_margin_risk(self, risk_data: Dict[str, Any]) -> None:
        """Store margin call risk score in database."""
        if not risk_data:
            return
        
        try:
            df = pd.DataFrame([risk_data])
            self.db.execute("INSERT OR REPLACE INTO margin_call_risk SELECT * FROM df")
            logger.info(f"Stored margin risk for {risk_data['ticker']}: {risk_data['composite_risk_score']:.1f}")
        except Exception as e:
            logger.error(f"Error storing margin risk: {e}")
    
    def calculate_and_store(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Calculate and store margin call risk for a ticker."""
        risk_data = self.calculate_composite_risk(ticker)
        
        if risk_data:
            self.store_margin_risk(risk_data)
            return risk_data
        
        return None
    
    def batch_calculate(self, tickers: list) -> Dict[str, Dict[str, Any]]:
        """Calculate margin call risk for multiple tickers."""
        results = {}
        
        for ticker in tickers:
            try:
                logger.info(f"Calculating margin call risk for {ticker}")
                risk_data = self.calculate_and_store(ticker)
                if risk_data:
                    results[ticker] = risk_data
            except Exception as e:
                logger.error(f"Error processing {ticker}: {e}")
        
        return results
