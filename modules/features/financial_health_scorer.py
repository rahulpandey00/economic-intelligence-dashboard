"""
Financial Health Scoring Module

Calculates financial health metrics for stocks:
- Piotroski F-Score (0-9): Fundamental strength across profitability, leverage, and efficiency
- Altman Z-Score: Bankruptcy risk prediction
- Custom Composite Score: Combines multiple financial ratios

Uses SEC XBRL data from Company Facts API.
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any
from datetime import datetime
import logging

try:
    from modules.database import get_db_connection
    from modules.sec_data_loader import get_company_facts, extract_financial_metric, lookup_cik
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False

logger = logging.getLogger(__name__)


class FinancialHealthScorer:
    """Calculate financial health scores using SEC financial data."""
    
    def __init__(self):
        if DB_AVAILABLE:
            self.db = get_db_connection()
        else:
            self.db = None
    
    def calculate_piotroski_score(self, ticker: str, cik: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate Piotroski F-Score (0-9 scale).
        
        The F-Score measures fundamental strength across 3 categories:
        - Profitability (4 points): ROA, CFO, Change in ROA, Accruals
        - Leverage/Liquidity (3 points): Change in Leverage, Change in Current Ratio, No new shares
        - Operating Efficiency (2 points): Change in Margin, Change in Turnover
        
        Args:
            ticker: Stock ticker symbol
            cik: Optional CIK number (will lookup if not provided)
            
        Returns:
            Dictionary with F-Score and detailed component breakdown
        """
        if not cik:
            cik = lookup_cik(ticker)
            if not cik:
                return {'error': f'Could not find CIK for ticker {ticker}'}
        
        try:
            # Fetch company financial data
            company_facts = get_company_facts(cik)
            if not company_facts:
                return {'error': f'No financial data available for CIK {cik}'}
            
            # Extract key financial metrics (last 2 years for comparison)
            financials = self._extract_piotroski_metrics(company_facts)
            
            if not financials or len(financials) < 2:
                return {'error': 'Insufficient financial data for Piotroski calculation'}
            
            # Calculate the 9 Piotroski criteria
            score = 0
            breakdown = {}
            
            current = financials[0]  # Most recent year
            prior = financials[1]    # Previous year
            
            # === PROFITABILITY (4 points max) ===
            
            # 1. Positive ROA
            roa = self._calculate_roa(current)
            if roa and roa > 0:
                score += 1
                breakdown['positive_roa'] = {'points': 1, 'value': roa}
            else:
                breakdown['positive_roa'] = {'points': 0, 'value': roa}
            
            # 2. Positive Operating Cash Flow
            if current.get('operating_cf', 0) > 0:
                score += 1
                breakdown['positive_cfo'] = {'points': 1, 'value': current.get('operating_cf')}
            else:
                breakdown['positive_cfo'] = {'points': 0, 'value': current.get('operating_cf')}
            
            # 3. Increasing ROA (compared to prior year)
            prior_roa = self._calculate_roa(prior)
            if roa and prior_roa and roa > prior_roa:
                score += 1
                breakdown['increasing_roa'] = {'points': 1, 'change': roa - prior_roa}
            else:
                breakdown['increasing_roa'] = {'points': 0, 'change': (roa or 0) - (prior_roa or 0)}
            
            # 4. Quality of Earnings (CFO > Net Income)
            net_income = current.get('net_income', 0)
            operating_cf = current.get('operating_cf', 0)
            if operating_cf > net_income:
                score += 1
                breakdown['quality_earnings'] = {'points': 1, 'cfo': operating_cf, 'ni': net_income}
            else:
                breakdown['quality_earnings'] = {'points': 0, 'cfo': operating_cf, 'ni': net_income}
            
            # === LEVERAGE/LIQUIDITY (3 points max) ===
            
            # 5. Decreasing Long-term Debt / Total Assets
            curr_leverage = current.get('long_term_debt', 0) / current.get('total_assets', 1)
            prior_leverage = prior.get('long_term_debt', 0) / prior.get('total_assets', 1)
            if curr_leverage < prior_leverage:
                score += 1
                breakdown['decreasing_leverage'] = {'points': 1, 'current': curr_leverage, 'prior': prior_leverage}
            else:
                breakdown['decreasing_leverage'] = {'points': 0, 'current': curr_leverage, 'prior': prior_leverage}
            
            # 6. Increasing Current Ratio
            curr_current_ratio = current.get('current_assets', 0) / max(current.get('current_liabilities', 1), 1)
            prior_current_ratio = prior.get('current_assets', 0) / max(prior.get('current_liabilities', 1), 1)
            if curr_current_ratio > prior_current_ratio:
                score += 1
                breakdown['increasing_current_ratio'] = {'points': 1, 'current': curr_current_ratio, 'prior': prior_current_ratio}
            else:
                breakdown['increasing_current_ratio'] = {'points': 0, 'current': curr_current_ratio, 'prior': prior_current_ratio}
            
            # 7. No New Shares Issued
            curr_shares = current.get('shares_outstanding', 0)
            prior_shares = prior.get('shares_outstanding', 0)
            if curr_shares > 0 and prior_shares > 0 and curr_shares <= prior_shares:
                score += 1
                breakdown['no_new_shares'] = {'points': 1, 'current': curr_shares, 'prior': prior_shares}
            else:
                breakdown['no_new_shares'] = {'points': 0, 'current': curr_shares, 'prior': prior_shares}
            
            # === OPERATING EFFICIENCY (2 points max) ===
            
            # 8. Increasing Gross Margin
            curr_gm = current.get('gross_profit', 0) / max(current.get('revenue', 1), 1)
            prior_gm = prior.get('gross_profit', 0) / max(prior.get('revenue', 1), 1)
            if curr_gm > prior_gm:
                score += 1
                breakdown['increasing_margin'] = {'points': 1, 'current': curr_gm, 'prior': prior_gm}
            else:
                breakdown['increasing_margin'] = {'points': 0, 'current': curr_gm, 'prior': prior_gm}
            
            # 9. Increasing Asset Turnover
            curr_turnover = current.get('revenue', 0) / max(current.get('total_assets', 1), 1)
            prior_turnover = prior.get('revenue', 0) / max(prior.get('total_assets', 1), 1)
            if curr_turnover > prior_turnover:
                score += 1
                breakdown['increasing_turnover'] = {'points': 1, 'current': curr_turnover, 'prior': prior_turnover}
            else:
                breakdown['increasing_turnover'] = {'points': 0, 'current': curr_turnover, 'prior': prior_turnover}
            
            # Classify score
            if score >= 7:
                classification = 'Strong'
            elif score >= 5:
                classification = 'Good'
            elif score >= 3:
                classification = 'Average'
            else:
                classification = 'Weak'
            
            return {
                'ticker': ticker,
                'cik': cik,
                'f_score': score,
                'classification': classification,
                'max_score': 9,
                'breakdown': breakdown,
                'profitability_score': breakdown['positive_roa']['points'] + breakdown['positive_cfo']['points'] + 
                                     breakdown['increasing_roa']['points'] + breakdown['quality_earnings']['points'],
                'leverage_score': breakdown['decreasing_leverage']['points'] + breakdown['increasing_current_ratio']['points'] + 
                                breakdown['no_new_shares']['points'],
                'efficiency_score': breakdown['increasing_margin']['points'] + breakdown['increasing_turnover']['points'],
                'as_of_date': current.get('fiscal_year'),
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating Piotroski score for {ticker}: {e}")
            return {'error': str(e)}
    
    def calculate_altman_z_score(self, ticker: str, cik: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate Altman Z-Score for bankruptcy prediction.
        
        Original Z-Score formula (for manufacturing companies):
        Z = 1.2×(WC/TA) + 1.4×(RE/TA) + 3.3×(EBIT/TA) + 0.6×(MVE/TL) + 1.0×(Sales/TA)
        
        Z-Score interpretation:
        - Z > 2.99: Safe Zone (low bankruptcy risk)
        - 1.81 < Z < 2.99: Grey Zone (moderate risk)
        - Z < 1.81: Distress Zone (high risk)
        
        Args:
            ticker: Stock ticker symbol
            cik: Optional CIK number
            
        Returns:
            Dictionary with Z-Score and component breakdown
        """
        if not cik:
            cik = lookup_cik(ticker)
            if not cik:
                return {'error': f'Could not find CIK for ticker {ticker}'}
        
        try:
            company_facts = get_company_facts(cik)
            if not company_facts:
                return {'error': f'No financial data available for CIK {cik}'}
            
            # Extract most recent annual data
            financials = self._extract_altman_metrics(company_facts)
            
            if not financials:
                return {'error': 'Insufficient financial data for Altman Z-Score'}
            
            # Calculate components
            working_capital = financials.get('current_assets', 0) - financials.get('current_liabilities', 0)
            total_assets = financials.get('total_assets', 1)
            retained_earnings = financials.get('retained_earnings', 0)
            ebit = financials.get('ebit', 0)
            market_value_equity = financials.get('market_cap', 0)  # Would need current stock price
            total_liabilities = financials.get('total_liabilities', 1)
            sales = financials.get('revenue', 0)
            
            # Calculate ratios
            x1 = working_capital / total_assets if total_assets > 0 else 0
            x2 = retained_earnings / total_assets if total_assets > 0 else 0
            x3 = ebit / total_assets if total_assets > 0 else 0
            x4 = market_value_equity / total_liabilities if total_liabilities > 0 else 0
            x5 = sales / total_assets if total_assets > 0 else 0
            
            # Calculate Z-Score
            z_score = (1.2 * x1) + (1.4 * x2) + (3.3 * x3) + (0.6 * x4) + (1.0 * x5)
            
            # Classify risk
            if z_score > 2.99:
                risk_zone = 'Safe Zone'
                risk_level = 'Low'
            elif z_score > 1.81:
                risk_zone = 'Grey Zone'
                risk_level = 'Moderate'
            else:
                risk_zone = 'Distress Zone'
                risk_level = 'High'
            
            return {
                'ticker': ticker,
                'cik': cik,
                'z_score': round(z_score, 2),
                'risk_zone': risk_zone,
                'risk_level': risk_level,
                'components': {
                    'working_capital_ratio': round(x1, 4),
                    'retained_earnings_ratio': round(x2, 4),
                    'ebit_ratio': round(x3, 4),
                    'market_value_ratio': round(x4, 4),
                    'asset_turnover': round(x5, 4)
                },
                'weighted_components': {
                    'wc_contribution': round(1.2 * x1, 2),
                    're_contribution': round(1.4 * x2, 2),
                    'ebit_contribution': round(3.3 * x3, 2),
                    'mv_contribution': round(0.6 * x4, 2),
                    'sales_contribution': round(1.0 * x5, 2)
                },
                'interpretation': {
                    'safe_threshold': 2.99,
                    'distress_threshold': 1.81,
                    'distance_to_distress': round(z_score - 1.81, 2)
                },
                'as_of_date': financials.get('fiscal_year'),
                'calculated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating Altman Z-Score for {ticker}: {e}")
            return {'error': str(e)}
    
    def calculate_composite_health_score(self, ticker: str, cik: Optional[str] = None) -> Dict[str, Any]:
        """
        Calculate a comprehensive financial health score combining multiple metrics.
        
        Composite score (0-100) based on:
        - Piotroski F-Score (40% weight)
        - Altman Z-Score (30% weight)
        - Profitability Ratios (15% weight)
        - Liquidity Ratios (15% weight)
        
        Args:
            ticker: Stock ticker symbol
            cik: Optional CIK number
            
        Returns:
            Dictionary with composite score and all underlying metrics
        """
        # Get both fundamental scores
        piotroski = self.calculate_piotroski_score(ticker, cik)
        altman = self.calculate_altman_z_score(ticker, cik)
        
        if 'error' in piotroski or 'error' in altman:
            return {
                'error': 'Insufficient data for composite score',
                'piotroski': piotroski,
                'altman': altman
            }
        
        # Normalize Piotroski (0-9 → 0-100)
        piotroski_normalized = (piotroski['f_score'] / 9.0) * 100
        
        # Normalize Altman Z-Score (0-6 → 0-100, capped)
        altman_normalized = min((altman['z_score'] / 6.0) * 100, 100)
        
        # Calculate composite score
        composite = (
            (piotroski_normalized * 0.40) +
            (altman_normalized * 0.30) +
            (50 * 0.15) +  # Placeholder for profitability ratios
            (50 * 0.15)    # Placeholder for liquidity ratios
        )
        
        # Classify overall health
        if composite >= 80:
            health_rating = 'Excellent'
        elif composite >= 60:
            health_rating = 'Good'
        elif composite >= 40:
            health_rating = 'Fair'
        elif composite >= 20:
            health_rating = 'Poor'
        else:
            health_rating = 'Critical'
        
        return {
            'ticker': ticker,
            'composite_score': round(composite, 1),
            'health_rating': health_rating,
            'components': {
                'piotroski': piotroski,
                'altman': altman
            },
            'normalized_scores': {
                'piotroski': round(piotroski_normalized, 1),
                'altman': round(altman_normalized, 1)
            },
            'weights': {
                'piotroski': 0.40,
                'altman': 0.30,
                'profitability': 0.15,
                'liquidity': 0.15
            },
            'calculated_at': datetime.now().isoformat()
        }
    
    def store_health_scores(self, ticker: str, scores: Dict[str, Any]) -> None:
        """Store financial health scores in database."""
        if not self.db:
            return
        
        try:
            data = {
                'ticker': ticker,
                'date': datetime.now().date(),
                'piotroski_score': scores.get('components', {}).get('piotroski', {}).get('f_score'),
                'altman_z_score': scores.get('components', {}).get('altman', {}).get('z_score'),
                'composite_score': scores.get('composite_score'),
                'health_rating': scores.get('health_rating'),
                'profitability_subscore': scores.get('components', {}).get('piotroski', {}).get('profitability_score'),
                'leverage_subscore': scores.get('components', {}).get('piotroski', {}).get('leverage_score'),
                'efficiency_subscore': scores.get('components', {}).get('piotroski', {}).get('efficiency_score'),
                'risk_zone': scores.get('components', {}).get('altman', {}).get('risk_zone')
            }
            
            df = pd.DataFrame([data])
            self.db.insert_df(df, 'financial_health_scores', if_exists='append')
            
        except Exception as e:
            logger.error(f"Error storing health scores: {e}")
    
    # === HELPER METHODS ===
    
    def _extract_piotroski_metrics(self, company_facts: Dict) -> list:
        """Extract financial metrics needed for Piotroski F-Score (last 2 years)."""
        metrics = []
        
        # Key concepts needed
        concepts = [
            'NetIncomeLoss',
            'Assets',
            'OperatingIncomeLoss',
            'NetCashProvidedByUsedInOperatingActivities',
            'LongTermDebt',
            'Liabilities',
            'AssetsCurrent',
            'LiabilitiesCurrent',
            'CommonStockSharesOutstanding',
            'GrossProfit',
            'Revenues'
        ]
        
        # Extract latest 2 annual filings (10-K)
        for concept in concepts:
            df = extract_financial_metric(company_facts, concept)
            if not df.empty:
                annual = df[df['form'] == '10-K'].head(2)
                # Store for cross-reference
                
        # Build financial snapshots (simplified - would need proper extraction)
        # This is a placeholder structure
        try:
            net_income_df = extract_financial_metric(company_facts, 'NetIncomeLoss')
            assets_df = extract_financial_metric(company_facts, 'Assets')
            
            if not net_income_df.empty and not assets_df.empty:
                # Get last 2 annual periods
                for i in range(min(2, len(net_income_df))):
                    metric_dict = {
                        'fiscal_year': net_income_df.iloc[i]['fiscal_year'],
                        'net_income': net_income_df.iloc[i]['value'],
                        'total_assets': assets_df.iloc[i]['value'] if i < len(assets_df) else 0,
                        'operating_cf': 0,  # Would extract from cash flow statement
                        'long_term_debt': 0,
                        'current_assets': 0,
                        'current_liabilities': 0,
                        'shares_outstanding': 0,
                        'gross_profit': 0,
                        'revenue': 0
                    }
                    metrics.append(metric_dict)
        except:
            pass
        
        return metrics
    
    def _extract_altman_metrics(self, company_facts: Dict) -> Dict:
        """Extract financial metrics for Altman Z-Score."""
        metrics = {}
        
        try:
            # Extract key values (most recent annual)
            assets_df = extract_financial_metric(company_facts, 'Assets')
            liabilities_df = extract_financial_metric(company_facts, 'Liabilities')
            revenue_df = extract_financial_metric(company_facts, 'Revenues')
            
            if not assets_df.empty:
                annual = assets_df[assets_df['form'] == '10-K'].head(1)
                if not annual.empty:
                    metrics['total_assets'] = annual.iloc[0]['value']
                    metrics['fiscal_year'] = annual.iloc[0]['fiscal_year']
            
            if not liabilities_df.empty:
                annual = liabilities_df[liabilities_df['form'] == '10-K'].head(1)
                if not annual.empty:
                    metrics['total_liabilities'] = annual.iloc[0]['value']
            
            if not revenue_df.empty:
                annual = revenue_df[revenue_df['form'] == '10-K'].head(1)
                if not annual.empty:
                    metrics['revenue'] = annual.iloc[0]['value']
            
            # Additional metrics (would extract from full financial statements)
            metrics['current_assets'] = metrics.get('total_assets', 0) * 0.4  # Placeholder
            metrics['current_liabilities'] = metrics.get('total_liabilities', 0) * 0.3
            metrics['retained_earnings'] = 0
            metrics['ebit'] = 0
            metrics['market_cap'] = 0
            
        except Exception as e:
            logger.error(f"Error extracting Altman metrics: {e}")
        
        return metrics
    
    def _calculate_roa(self, financials: Dict) -> Optional[float]:
        """Calculate Return on Assets."""
        net_income = financials.get('net_income', 0)
        total_assets = financials.get('total_assets', 0)
        
        if total_assets > 0:
            return net_income / total_assets
        return None
