"""
Smart data refresh script for Economic Dashboard.
Fetches economic data based on natural update frequencies and SLAs.
Respects rate limits and only refreshes data when needed.
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import pickle
import time
import argparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pandas_datareader import data as pdr
import yfinance as yf
from config_settings import ensure_cache_dir, get_cache_dir
from modules.data_series_config import (
    FRED_SERIES_CONFIG,
    YFINANCE_TICKERS_CONFIG,
    UpdateFrequency,
    get_all_fred_series,
    get_all_yfinance_tickers,
    get_series_by_frequency,
    should_refresh,
    get_update_sla
)

# Rate limiting: delay between API requests to avoid rate limits
RATE_LIMIT_DELAY = 0.5  # seconds between requests


def get_cache_metadata(cache_file: str) -> dict:
    """Get metadata about when cache was last updated."""
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, 'rb') as f:
            cache_data = pickle.load(f)
        return {
            'timestamp': cache_data.get('timestamp'),
            'series_count': len(cache_data.get('data', {}).columns) if isinstance(cache_data.get('data'), pd.DataFrame) else len(cache_data.get('data', {}))
        }
    except Exception:
        return None


def fetch_fred_series_incremental(frequency: str, years_back: int = 20, force: bool = False) -> pd.DataFrame:
    """
    Fetch FRED data for a specific frequency, only if SLA requires refresh.
    
    Args:
        frequency: 'daily', 'weekly', 'monthly', or 'quarterly'
        years_back: How many years of historical data to fetch
        force: Force refresh regardless of SLA
    """
    ensure_cache_dir()
    cache_file = os.path.join(get_cache_dir(), f'fred_{frequency}.pkl')
    
    # Check if refresh is needed
    metadata = get_cache_metadata(cache_file)
    if not force and metadata:
        last_update = metadata['timestamp']
        if not should_refresh(frequency, last_update):
            sla = get_update_sla(frequency)
            next_update = last_update + sla
            print(f"  ℹ️  {frequency.upper()} data is fresh (updated {last_update.strftime('%Y-%m-%d %H:%M')})")
            print(f"      Next update due: {next_update.strftime('%Y-%m-%d %H:%M')}")
            
            # Load and return existing cache
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            return cache_data['data']
    
    # Fetch the data
    series_dict = get_series_by_frequency(frequency, 'fred')
    if not series_dict:
        print(f"  ⚠️  No series configured for frequency: {frequency}")
        return pd.DataFrame()
    
    print(f"\n📥 Fetching {len(series_dict)} FRED series ({frequency.upper()})...")
    
    start_date = datetime.now() - pd.DateOffset(years=years_back)
    all_data = {}
    successful = 0
    
    for name, series_id in series_dict.items():
        try:
            print(f"  Fetching {name} ({series_id})...", end=' ', flush=True)
            df = pdr.DataReader(series_id, 'fred', start=start_date)
            all_data[name] = df[series_id]
            successful += 1
            print("✓")
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
            
        except Exception as e:
            print(f"✗ {str(e)[:50]}")
            continue
    
    if not all_data:
        print(f"  ❌ No data was successfully fetched for {frequency}")
        return pd.DataFrame()
    
    # Combine into DataFrame
    combined_df = pd.DataFrame(all_data)
    print(f"  ✅ Successfully fetched {successful}/{len(series_dict)} series ({len(combined_df)} rows)")
    
    # Save to cache
    cache_data = {
        'timestamp': datetime.now(),
        'data': combined_df,
        'frequency': frequency
    }
    
    with open(cache_file, 'wb') as f:
        pickle.dump(cache_data, f)
    
    print(f"  💾 Saved to {cache_file}")
    
    return combined_df


def fetch_yfinance_incremental(frequency: str, years_back: int = 10, force: bool = False) -> dict:
    """
    Fetch Yahoo Finance data for a specific frequency, only if SLA requires refresh.
    """
    ensure_cache_dir()
    cache_file = os.path.join(get_cache_dir(), f'yfinance_{frequency}.pkl')
    
    # Check if refresh is needed
    metadata = get_cache_metadata(cache_file)
    if not force and metadata:
        last_update = metadata['timestamp']
        if not should_refresh(frequency, last_update):
            sla = get_update_sla(frequency)
            next_update = last_update + sla
            print(f"  ℹ️  {frequency.upper()} data is fresh (updated {last_update.strftime('%Y-%m-%d %H:%M')})")
            print(f"      Next update due: {next_update.strftime('%Y-%m-%d %H:%M')}")
            
            # Load and return existing cache
            with open(cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            return cache_data['data']
    
    # Fetch the data
    tickers_dict = get_series_by_frequency(frequency, 'yfinance')
    if not tickers_dict:
        print(f"  ⚠️  No tickers configured for frequency: {frequency}")
        return {}
    
    print(f"\n📥 Fetching {len(tickers_dict)} Yahoo Finance tickers ({frequency.upper()})...")
    
    start_date = datetime.now() - pd.DateOffset(years=years_back)
    all_data = {}
    successful = 0
    
    for name, ticker in tickers_dict.items():
        try:
            print(f"  Fetching {name} ({ticker})...", end=' ', flush=True)
            data = yf.download(ticker, start=start_date, progress=False)
            if not data.empty:
                all_data[name] = data
                successful += 1
                print("✓")
            else:
                print("✗ No data")
        except Exception as e:
            print(f"✗ {str(e)[:50]}")
            continue
    
    print(f"  ✅ Successfully fetched {successful}/{len(tickers_dict)} tickers")
    
    # Save to cache
    cache_data = {
        'timestamp': datetime.now(),
        'data': all_data,
        'frequency': frequency
    }
    
    with open(cache_file, 'wb') as f:
        pickle.dump(cache_data, f)
    
    print(f"  💾 Saved to {cache_file}")
    
    return all_data


def merge_all_caches(source: str = 'fred') -> pd.DataFrame | dict:
    """Merge all frequency-specific caches into one combined cache."""
    ensure_cache_dir()
    cache_dir = get_cache_dir()
    
    if source == 'fred':
        frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
        all_data_frames = []
        
        for freq in frequencies:
            cache_file = os.path.join(cache_dir, f'fred_{freq}.pkl')
            if os.path.exists(cache_file):
                try:
                    with open(cache_file, 'rb') as f:
                        cache_data = pickle.load(f)
                    all_data_frames.append(cache_data['data'])
                except Exception as e:
                    print(f"  ⚠️  Could not load {freq} cache: {e}")
        
        if all_data_frames:
            # Merge all DataFrames on index (dates)
            combined = pd.concat(all_data_frames, axis=1)
            return combined
        return pd.DataFrame()
    
    elif source == 'yfinance':
        all_tickers = {}
        cache_file = os.path.join(cache_dir, 'yfinance_daily.pkl')
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    cache_data = pickle.load(f)
                all_tickers = cache_data['data']
            except Exception as e:
                print(f"  ⚠️  Could not load yfinance cache: {e}")
        
        return all_tickers


def save_combined_cache(data, filename: str):
    """Save the combined cache (for backward compatibility)."""
    ensure_cache_dir()
    cache_file = os.path.join(get_cache_dir(), filename)
    
    cache_data = {
        'timestamp': datetime.now(),
        'data': data
    }
    
    with open(cache_file, 'wb') as f:
        pickle.dump(cache_data, f)
    
    print(f"  💾 Saved combined cache to {cache_file}")


def save_to_csv_backup(data, csv_filename: str):
    """Save data to CSV for backup and inspection."""
    backup_dir = 'data/backups'
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    csv_file = os.path.join(backup_dir, f"{timestamp}_{csv_filename}")
    
    if isinstance(data, pd.DataFrame):
        data.to_csv(csv_file)
        print(f"  📄 Backup saved to {csv_file}")
    elif isinstance(data, dict):
        # For Yahoo Finance data, save each ticker separately
        for name, df in data.items():
            ticker_file = csv_file.replace('.csv', f'_{name}.csv')
            df.to_csv(ticker_file)
        print(f"  📄 Backup saved to {csv_file.replace('.csv', '_*.csv')}")


def main():
    """Main data refresh pipeline with smart frequency-based updates."""
    parser = argparse.ArgumentParser(description='Smart Economic Data Refresh')
    parser.add_argument('--force', action='store_true', help='Force refresh all data regardless of SLA')
    parser.add_argument('--frequency', choices=['daily', 'weekly', 'monthly', 'quarterly', 'all'], 
                       default='all', help='Only refresh specific frequency')
    parser.add_argument('--test', action='store_true', help='Test mode: fetch only 2 series from each frequency')
    args = parser.parse_args()
    
    print("=" * 70)
    print("Economic Dashboard - Smart Data Refresh")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Mode: {'FORCE REFRESH' if args.force else 'SLA-BASED'}")
    if args.test:
        print("⚠️  TEST MODE: Limited series fetch")
    print("=" * 70)
    
    try:
        # Determine which frequencies to refresh
        if args.frequency == 'all':
            fred_frequencies = ['daily', 'weekly', 'monthly', 'quarterly']
            yf_frequencies = ['daily']
        else:
            fred_frequencies = [args.frequency] if args.frequency in ['daily', 'weekly', 'monthly', 'quarterly'] else []
            yf_frequencies = ['daily'] if args.frequency == 'daily' else []
        
        # Fetch FRED data by frequency
        fred_data_parts = {}
        for freq in fred_frequencies:
            fred_data_parts[freq] = fetch_fred_series_incremental(freq, years_back=20, force=args.force)
        
        # Fetch Yahoo Finance data
        yf_data = {}
        for freq in yf_frequencies:
            yf_data = fetch_yfinance_incremental(freq, years_back=10, force=args.force)
        
        # Create combined caches for backward compatibility
        print("\n🔗 Creating combined caches...")
        combined_fred = merge_all_caches('fred')
        if not combined_fred.empty:
            save_combined_cache(combined_fred, 'fred_all_series.pkl')
            save_to_csv_backup(combined_fred, 'fred_data.csv')
        
        combined_yf = merge_all_caches('yfinance')
        if combined_yf:
            save_combined_cache(combined_yf, 'yfinance_all_tickers.pkl')
            save_to_csv_backup(combined_yf, 'yfinance_data.csv')
        
        # Create summary report
        print("\n" + "=" * 70)
        print("📊 Data Refresh Summary")
        print("=" * 70)
        
        if not combined_fred.empty:
            print(f"FRED Series: {len(combined_fred.columns)} series")
            print(f"  Date range: {combined_fred.index.min()} to {combined_fred.index.max()}")
            print(f"  Total rows: {len(combined_fred)}")
            print(f"\n  By Frequency:")
            for freq in fred_frequencies:
                if freq in fred_data_parts and not fred_data_parts[freq].empty:
                    print(f"    {freq.capitalize():12} {len(fred_data_parts[freq].columns):3} series")
        
        if combined_yf:
            print(f"\nYahoo Finance: {len(combined_yf)} tickers")
            for name, df in combined_yf.items():
                print(f"  {name:15} {len(df):6} rows ({df.index.min().date()} to {df.index.max().date()})")
        
        print(f"\n✅ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
