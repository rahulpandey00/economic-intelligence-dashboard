"""
Airflow DAG for daily Economic Dashboard data refresh.

This DAG runs daily to fetch economic data from FRED and Yahoo Finance,
stores it in cache, and creates backups.

Requirements:
    - Apache Airflow 2.x
    - pip install pandas-datareader yfinance pandas
"""

from datetime import datetime, timedelta
from pathlib import Path
import sys

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.utils.dates import days_ago

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# Default arguments
default_args = {
    'owner': 'economic-dashboard',
    'depends_on_past': False,
    'email': ['your-email@example.com'],  # Update this
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'execution_timeout': timedelta(minutes=30),
}


def run_data_refresh():
    """Execute the data refresh script."""
    from scripts.refresh_data import main
    
    result = main()
    if result != 0:
        raise Exception("Data refresh script failed")
    
    return "Data refresh completed successfully"


def validate_data_quality():
    """Validate that the refreshed data meets quality standards."""
    import pandas as pd
    import pickle
    from config import get_cache_dir
    import os
    
    cache_dir = get_cache_dir()
    fred_cache = os.path.join(cache_dir, 'fred_all_series.pkl')
    yf_cache = os.path.join(cache_dir, 'yfinance_all_tickers.pkl')
    
    issues = []
    
    # Check FRED data
    if not os.path.exists(fred_cache):
        issues.append("FRED cache file not found")
    else:
        with open(fred_cache, 'rb') as f:
            cache_data = pickle.load(f)
            fred_df = cache_data['data']
            
            if len(fred_df) < 100:
                issues.append(f"FRED data has only {len(fred_df)} rows (expected >100)")
            
            if len(fred_df.columns) < 30:
                issues.append(f"FRED data has only {len(fred_df.columns)} series (expected >30)")
            
            # Check for recent data (within last 30 days)
            if fred_df.index.max() < datetime.now() - timedelta(days=30):
                issues.append(f"FRED data is stale (latest: {fred_df.index.max()})")
    
    # Check Yahoo Finance data
    if not os.path.exists(yf_cache):
        issues.append("Yahoo Finance cache file not found")
    else:
        with open(yf_cache, 'rb') as f:
            cache_data = pickle.load(f)
            yf_data = cache_data['data']
            
            if len(yf_data) < 3:
                issues.append(f"Yahoo Finance has only {len(yf_data)} tickers (expected ≥5)")
    
    if issues:
        raise Exception(f"Data quality validation failed: {'; '.join(issues)}")
    
    return "Data quality validation passed"


def send_success_notification():
    """Send notification about successful data refresh."""
    # Implement your notification logic here
    # Examples: Slack, Email, Teams, etc.
    print("✅ Data refresh completed successfully!")
    return "Notification sent"


# Define the DAG
with DAG(
    'economic_dashboard_data_refresh',
    default_args=default_args,
    description='Daily refresh of economic data for dashboard',
    schedule_interval='0 6 * * *',  # Daily at 6 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['economic-dashboard', 'data-refresh'],
) as dag:
    
    # Task 1: Create necessary directories
    create_dirs = BashOperator(
        task_id='create_directories',
        bash_command='mkdir -p data/cache data/backups',
    )
    
    # Task 2: Run data refresh
    refresh_data = PythonOperator(
        task_id='refresh_economic_data',
        python_callable=run_data_refresh,
    )
    
    # Task 3: Validate data quality
    validate_data = PythonOperator(
        task_id='validate_data_quality',
        python_callable=validate_data_quality,
    )
    
    # Task 4: Clean old backups (keep last 30 days)
    cleanup_old_backups = BashOperator(
        task_id='cleanup_old_backups',
        bash_command='find data/backups -name "*.csv" -mtime +30 -delete',
    )
    
    # Task 5: Send success notification
    notify_success = PythonOperator(
        task_id='notify_success',
        python_callable=send_success_notification,
    )
    
    # Define task dependencies
    create_dirs >> refresh_data >> validate_data >> cleanup_old_backups >> notify_success


# Optional: Create a separate DAG for weekly full refresh with extended history
with DAG(
    'economic_dashboard_weekly_full_refresh',
    default_args=default_args,
    description='Weekly full refresh with extended historical data',
    schedule_interval='0 3 * * 0',  # Sundays at 3 AM UTC
    start_date=days_ago(1),
    catchup=False,
    tags=['economic-dashboard', 'weekly-refresh'],
) as weekly_dag:
    
    def run_extended_refresh():
        """Run data refresh with extended historical period."""
        from scripts.refresh_data import fetch_fred_data, fetch_yfinance_data, save_to_cache, FRED_SERIES, YFINANCE_TICKERS
        
        # Fetch extended history (30 years for FRED, 15 for Yahoo)
        fred_data = fetch_fred_data(FRED_SERIES, years_back=30)
        save_to_cache(fred_data, 'fred_all_series_extended.pkl')
        
        yf_data = fetch_yfinance_data(YFINANCE_TICKERS, years_back=15)
        save_to_cache(yf_data, 'yfinance_all_tickers_extended.pkl')
        
        return "Extended refresh completed"
    
    weekly_refresh = PythonOperator(
        task_id='weekly_extended_refresh',
        python_callable=run_extended_refresh,
    )
