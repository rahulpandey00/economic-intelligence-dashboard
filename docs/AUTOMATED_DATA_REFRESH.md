# Automated Data Refresh Setup Guide

This guide explains how to set up automated daily data refresh for the Economic Dashboard using either GitHub Actions (recommended) or Apache Airflow.

## Overview

The automated data refresh system:
- Runs daily at 6 AM UTC (1 AM EST)
- Fetches all economic data from FRED (40+ series) and Yahoo Finance (5+ tickers)
- Stores data in a centralized cache (`data/cache/`)
- Creates CSV backups for inspection (`data/backups/`)
- Can be triggered manually when needed

## Architecture

```
┌─────────────────────┐
│  GitHub Actions     │
│  or Airflow         │
└──────────┬──────────┘
           │ triggers
           ▼
┌─────────────────────┐
│ refresh_data.py     │
│ - Fetch FRED data   │
│ - Fetch YF data     │
│ - Create cache      │
└──────────┬──────────┘
           │ saves to
           ▼
┌─────────────────────┐
│ Centralized Cache   │
│ fred_all_series.pkl │
│ yfinance_all.pkl    │
└──────────┬──────────┘
           │ used by
           ▼
┌─────────────────────┐
│  Streamlit App      │
│  (data_loader.py)   │
└─────────────────────┘
```

## Option 1: GitHub Actions (Recommended)

### Benefits
- ✅ No infrastructure needed
- ✅ Free for public repos
- ✅ Runs in the cloud
- ✅ Easy to monitor via GitHub UI
- ✅ Version controlled data updates

### Setup Steps

1. **Ensure workflow file exists** (already created):
   ```
   .github/workflows/data-refresh.yml
   ```

2. **Configure secrets** (if using FRED API key):
   - Go to GitHub repository → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `FRED_API_KEY`
   - Value: Your FRED API key
   - Click "Add secret"

3. **Enable GitHub Actions**:
   - Go to repository → Actions tab
   - If Actions are disabled, click "I understand my workflows, go ahead and enable them"

4. **Test the workflow**:
   ```bash
   # Trigger manually from GitHub UI:
   # Go to Actions → Daily Data Refresh → Run workflow → Run workflow
   
   # Or push a change to trigger:
   git add .
   git commit -m "Enable automated data refresh"
   git push
   ```

5. **Monitor execution**:
   - Go to Actions tab
   - Click on the workflow run to see logs
   - Check the "Data Refresh Summary" for status

### Scheduling

The workflow runs:
- **Daily**: 6 AM UTC (1 AM EST / 10 PM PST)
- **Manual**: Can be triggered via GitHub UI
- **On push**: When `scripts/refresh_data.py` or workflow file changes

To change the schedule, edit `.github/workflows/data-refresh.yml`:
```yaml
schedule:
  - cron: '0 6 * * *'  # Change this cron expression
```

### Data Storage

GitHub Actions stores data in two ways:
1. **Git commits**: Data is committed back to the repository
2. **Artifacts**: Cached data is uploaded as workflow artifacts (30-day retention)

To **disable git commits** (use only artifacts), comment out the commit step:
```yaml
# - name: Commit and push updated data
#   if: steps.check_changes.outputs.changes == 'true'
#   run: |
#     git config --local user.email "github-actions[bot]@users.noreply.github.com"
#     git config --local user.name "github-actions[bot]"
#     git add data/cache data/backups
#     git commit -m "chore: daily data refresh $(date +'%Y-%m-%d %H:%M UTC')"
#     git push
```

---

## Option 2: Apache Airflow

### Benefits
- ✅ More flexible scheduling
- ✅ Better for complex data pipelines
- ✅ Advanced monitoring and alerting
- ✅ Can integrate with databases

### Prerequisites

```bash
# Install Airflow
pip install apache-airflow==2.7.0

# Install providers
pip install apache-airflow-providers-email
```

### Setup Steps

1. **Initialize Airflow**:
   ```bash
   # Set Airflow home
   export AIRFLOW_HOME=~/airflow
   
   # Initialize database
   airflow db init
   
   # Create admin user
   airflow users create \
       --username admin \
       --password admin \
       --firstname Admin \
       --lastname User \
       --role Admin \
       --email admin@example.com
   ```

2. **Copy DAG file**:
   ```bash
   # Link or copy the DAG to Airflow's DAG folder
   cp airflow/dags/economic_data_refresh_dag.py ~/airflow/dags/
   ```

3. **Configure email notifications** (optional):
   Edit `~/airflow/airflow.cfg`:
   ```ini
   [smtp]
   smtp_host = smtp.gmail.com
   smtp_starttls = True
   smtp_ssl = False
   smtp_user = your-email@gmail.com
   smtp_password = your-app-password
   smtp_port = 587
   smtp_mail_from = your-email@gmail.com
   ```

   Update the DAG file with your email:
   ```python
   default_args = {
       'email': ['your-email@example.com'],  # Change this
       ...
   }
   ```

4. **Start Airflow**:
   ```bash
   # Start the web server (in one terminal)
   airflow webserver --port 8080
   
   # Start the scheduler (in another terminal)
   airflow scheduler
   ```

5. **Access Airflow UI**:
   - Open browser: http://localhost:8080
   - Login with credentials created in step 1
   - Enable the `economic_dashboard_data_refresh` DAG

### DAG Features

The DAG includes:
- **Daily refresh**: Runs at 6 AM UTC
- **Data validation**: Checks data quality after fetch
- **Cleanup**: Removes backups older than 30 days
- **Notifications**: Sends alerts on success/failure
- **Weekly full refresh**: Extended historical data on Sundays

### Monitoring

View DAG execution:
```bash
# List all DAG runs
airflow dags list-runs -d economic_dashboard_data_refresh

# View task logs
airflow tasks logs economic_dashboard_data_refresh refresh_economic_data 2024-01-15
```

---

## Manual Execution

To run the data refresh manually (without GitHub Actions or Airflow):

```bash
# Activate your virtual environment
.venv\Scripts\Activate.ps1  # Windows
# or
source .venv/bin/activate  # Linux/Mac

# Run the refresh script
python scripts/refresh_data.py
```

Expected output:
```
============================================================
Economic Dashboard - Daily Data Refresh
Started at: 2024-01-15 06:00:00
============================================================
Fetching 40 FRED series...
  Fetching GDP (GDP)... ✓
  Fetching Real GDP (GDPC1)... ✓
  ...
Successfully fetched 40 series with 8000 rows
Saved to data/cache/fred_all_series.pkl
Backup saved to data/backups/20240115_060000_fred_data.csv

Fetching 5 Yahoo Finance tickers...
  Fetching S&P 500 (^GSPC)... ✓
  ...
Successfully fetched 5 tickers
Saved to data/cache/yfinance_all_tickers.pkl
============================================================
```

---

## Data Cache Structure

```
data/
├── cache/                          # Live cache used by app
│   ├── fred_all_series.pkl        # Centralized FRED cache
│   ├── yfinance_all_tickers.pkl   # Centralized Yahoo Finance cache
│   ├── fred_*.pkl                 # Individual series caches (fallback)
│   └── yfinance_*.pkl             # Individual ticker caches (fallback)
│
└── backups/                        # CSV backups for inspection
    ├── 20240115_060000_fred_data.csv
    ├── 20240115_060000_yfinance_data_S&P 500.csv
    └── ...
```

### Cache Priority

The app uses this priority order:
1. **Centralized cache** (`fred_all_series.pkl`) - Updated daily by automation
2. **Individual cache** (`fred_<hash>.pkl`) - Created on-demand by app
3. **FRED API** - Live fetch if cache expired
4. **Offline sample data** - Fallback if API unavailable

---

## Troubleshooting

### GitHub Actions Issues

**Workflow not running:**
```bash
# Check if Actions are enabled
# GitHub repo → Settings → Actions → General → Allow all actions

# Check workflow syntax
gh workflow view data-refresh.yml
```

**Data not committing back:**
```bash
# Ensure GITHUB_TOKEN has write permissions
# .github/workflows/data-refresh.yml should have:
permissions:
  contents: write
```

**Rate limiting errors:**
- Add FRED API key to secrets
- Use the API key in the script

### Airflow Issues

**DAG not showing up:**
```bash
# Check for syntax errors
python -m py_compile airflow/dags/economic_data_refresh_dag.py

# Refresh DAGs
airflow dags list-import-errors
```

**Tasks failing:**
```bash
# Check logs
airflow tasks logs economic_dashboard_data_refresh refresh_economic_data <date>

# Test task individually
airflow tasks test economic_dashboard_data_refresh refresh_economic_data 2024-01-15
```

### Data Quality Issues

**Cache is stale:**
```python
# Check cache age
import pickle
from datetime import datetime

with open('data/cache/fred_all_series.pkl', 'rb') as f:
    cache = pickle.load(f)
    print(f"Cache timestamp: {cache['timestamp']}")
    print(f"Age: {datetime.now() - cache['timestamp']}")
```

**Missing series:**
```python
# Check what's in cache
import pickle
with open('data/cache/fred_all_series.pkl', 'rb') as f:
    cache = pickle.load(f)
    print(f"Available series: {cache['data'].columns.tolist()}")
```

---

## Production Recommendations

1. **Use GitHub Actions for simplicity**:
   - Perfect for small to medium dashboards
   - No infrastructure costs
   - Easy to maintain

2. **Use Airflow for scale**:
   - Better for multiple data pipelines
   - More control over execution
   - Advanced monitoring

3. **Add monitoring**:
   - Set up email alerts for failures
   - Monitor cache age in the app
   - Track data freshness metrics

4. **Optimize costs**:
   - FRED API has rate limits (120 calls/min)
   - Consider caching strategy for high-traffic apps
   - Use artifacts instead of git commits for large datasets

5. **Backup strategy**:
   - Keep CSV backups for 30 days
   - Export to S3/Azure Blob for long-term storage
   - Version control cache updates

---

## Next Steps

- [ ] Choose deployment method (GitHub Actions or Airflow)
- [ ] Configure API keys and secrets
- [ ] Test manual execution
- [ ] Enable automated workflow
- [ ] Monitor first automated run
- [ ] Set up alerting for failures
- [ ] Document your specific configuration

## Support

For issues:
1. Check workflow logs (GitHub Actions → Workflow run)
2. Review Airflow task logs (`airflow tasks logs ...`)
3. Run script manually to isolate issues
4. Check FRED API status: https://fred.stlouisfed.org/docs/api/fred/
