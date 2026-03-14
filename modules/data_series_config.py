"""
Data series configuration with update frequencies and SLAs.
Defines when each economic indicator should be refreshed based on its natural publication schedule.
"""

from datetime import timedelta

# Update frequency definitions
class UpdateFrequency:
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    QUARTERLY = 'quarterly'


# SLA definitions: how long data can be cached before refresh is needed
UPDATE_SLA = {
    UpdateFrequency.DAILY: timedelta(hours=6),      # Refresh every 6 hours
    UpdateFrequency.WEEKLY: timedelta(days=1),      # Refresh daily
    UpdateFrequency.MONTHLY: timedelta(days=7),     # Refresh weekly
    UpdateFrequency.QUARTERLY: timedelta(days=30),  # Refresh monthly
}


# FRED series configuration with metadata
FRED_SERIES_CONFIG = {
    # DAILY UPDATE - Market rates and financial indicators
    'daily': {
        'frequency': UpdateFrequency.DAILY,
        'description': 'Updated daily by markets/Fed',
        'series': {
            # Interest Rates & Treasury Yields
            'Federal Funds Rate': 'FEDFUNDS',
            '10Y Treasury': 'DGS10',
            '2Y Treasury': 'DGS2',
            '5Y Treasury': 'DGS5',
            '30Y Treasury': 'DGS30',
            '10Y-2Y Spread': 'T10Y2Y',
            'Prime Rate': 'DPRIME',
            '30Y Mortgage Rate': 'MORTGAGE30US',
        }
    },
    
    # WEEKLY UPDATE - Labor market indicators
    'weekly': {
        'frequency': UpdateFrequency.WEEKLY,
        'description': 'Updated weekly (Thursday mornings)',
        'series': {
            # Jobless Claims
            'Initial Jobless Claims': 'ICSA',
            '4-Week MA Claims': 'IC4WSA',
        }
    },
    
    # MONTHLY UPDATE - Most economic indicators
    'monthly': {
        'frequency': UpdateFrequency.MONTHLY,
        'description': 'Updated monthly by BLS/Census/Fed',
        'series': {
            # Employment & Labor
            'Unemployment Rate': 'UNRATE',
            'Nonfarm Payrolls': 'PAYEMS',
            'Labor Force Participation': 'CIVPART',
            'Employment-Population Ratio': 'EMRATIO',
            'Average Hourly Earnings': 'CES0500000003',
            'Job Openings': 'JTSJOL',
            
            # Inflation & Prices
            'CPI All Items': 'CPIAUCSL',
            'Core CPI': 'CPILFESL',
            'PCE Price Index': 'PCEPI',
            'Core PCE': 'PCEPILFE',
            'PPI Final Demand': 'PPIFGS',
            'Import Price Index': 'IR',
            'Food CPI': 'CPIUFDSL',
            
            # Consumer & Housing
            'Personal Consumption Expenditures': 'PCE',
            'Real PCE': 'PCEC96',
            'Personal Saving Rate': 'PSAVERT',
            'Retail Sales': 'RSXFS',
            'Housing Starts': 'HOUST',
            'Home Prices (Case-Shiller)': 'CSUSHPISA',
            'New Home Sales': 'HSN1F',
            
            # Monetary Aggregates
            'M2 Money Supply': 'M2SL',
            
            # Expectations
            '5Y Inflation Expectations': 'T5YIE',
        }
    },
    
    # QUARTERLY UPDATE - GDP and productivity
    'quarterly': {
        'frequency': UpdateFrequency.QUARTERLY,
        'description': 'Updated quarterly by BEA',
        'series': {
            # GDP & Components
            'GDP': 'GDP',
            'Real GDP': 'GDPC1',
            'GDP Growth Rate': 'A191RL1Q225SBEA',
            'Real GDP per Capita': 'A939RX0Q048SBEA',
            'Personal Consumption': 'PCEQ',  # Quarterly version
            'Private Investment': 'GPDIC1',
            'Government Spending': 'GCEC1',
            
            # Productivity
            'Labor Productivity': 'OPHNFB',
            'Non-Farm Productivity': 'PNFI',
        }
    }
}


# Yahoo Finance tickers configuration
YFINANCE_TICKERS_CONFIG = {
    'daily': {
        'frequency': UpdateFrequency.DAILY,
        'description': 'Market data updated in real-time',
        'tickers': {
            'S&P 500': '^GSPC',
            'VIX': '^VIX',
            'USD Index': 'DX-Y.NYB',
            'Gold': 'GC=F',
            'Crude Oil': 'CL=F',
        }
    }
}


def get_all_fred_series() -> dict:
    """Get all FRED series as a single dictionary."""
    all_series = {}
    for category_config in FRED_SERIES_CONFIG.values():
        all_series.update(category_config['series'])
    return all_series


def get_all_yfinance_tickers() -> dict:
    """Get all Yahoo Finance tickers as a single dictionary."""
    all_tickers = {}
    for category_config in YFINANCE_TICKERS_CONFIG.values():
        all_tickers.update(category_config['tickers'])
    return all_tickers


def get_series_by_frequency(frequency: str, source: str = 'fred') -> dict:
    """Get series that should be updated at the given frequency."""
    if source == 'fred':
        config = FRED_SERIES_CONFIG.get(frequency, {})
    elif source == 'yfinance':
        config = YFINANCE_TICKERS_CONFIG.get(frequency, {})
    else:
        return {}
    
    return config.get('series' if source == 'fred' else 'tickers', {})


def get_update_sla(frequency: str) -> timedelta:
    """Get the SLA (max cache age) for a given update frequency."""
    return UPDATE_SLA.get(frequency, timedelta(days=1))


def should_refresh(frequency: str, last_update_time) -> bool:
    """Determine if data at this frequency should be refreshed."""
    from datetime import datetime
    
    if last_update_time is None:
        return True
    
    sla = get_update_sla(frequency)
    time_since_update = datetime.now() - last_update_time
    
    return time_since_update >= sla
