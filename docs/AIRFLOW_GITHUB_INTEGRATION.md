# Airflow + GitHub Integration Guide

This guide explains how to deploy and trigger Apache Airflow DAGs using GitHub Actions.

## Architecture Overview

```
┌─────────────────────┐
│  GitHub Actions     │
│  (Scheduler)        │
└──────────┬──────────┘
           │ triggers via API
           ▼
┌─────────────────────┐
│  Airflow Server     │
│  - Webserver        │
│  - Scheduler        │
│  - Worker(s)        │
└──────────┬──────────┘
           │ executes
           ▼
┌─────────────────────┐
│  Data Refresh DAG   │
│  - Fetch FRED       │
│  - Fetch Yahoo      │
│  - Validate         │
│  - Cache            │
└─────────────────────┘
```

## Deployment Options

### Option 1: Self-Hosted Airflow + GitHub Triggers (Recommended)

**Pros:**
- Full control over Airflow
- No vendor lock-in
- Free for infrastructure you already have
- Easy to test locally

**Cons:**
- Requires maintaining Airflow server
- Need to handle security and updates

**Setup:**

1. **Install Airflow on your server** (Linux, EC2, DigitalOcean, etc.):
   ```bash
   # On your server
   pip install apache-airflow==2.7.0
   airflow db init
   airflow users create \
       --username admin \
       --password admin123 \
       --firstname Admin \
       --lastname User \
       --role Admin \
       --email admin@example.com
   
   # Start services
   airflow webserver -p 8080 &
   airflow scheduler &
   ```

2. **Enable Airflow REST API**:
   Edit `~/airflow/airflow.cfg`:
   ```ini
   [api]
   auth_backend = airflow.api.auth.backend.basic_auth
   ```

3. **Deploy DAG files**:
   ```bash
   # Copy DAGs to Airflow
   scp airflow/dags/economic_data_refresh_dag.py \
       user@your-server:~/airflow/dags/
   ```

4. **Configure GitHub Secrets**:
   Go to GitHub repo → Settings → Secrets and variables → Actions:
   - `AIRFLOW_URL`: `http://your-server:8080`
   - `AIRFLOW_USERNAME`: `admin`
   - `AIRFLOW_PASSWORD`: Your Airflow password

5. **Trigger from GitHub**:
   The workflow `.github/workflows/trigger-airflow-dag.yml` will:
   - Run daily at 6 AM UTC
   - Call Airflow REST API to trigger DAG
   - Monitor execution status
   - Report results

---

### Option 2: Astronomer (Managed Airflow)

**Pros:**
- Fully managed Airflow
- Built-in GitHub integration
- Auto-scaling
- Enterprise support

**Cons:**
- Costs money (~$110/month for basic)
- Vendor lock-in

**Setup:**

1. **Sign up for Astronomer**: https://www.astronomer.io/

2. **Install Astronomer CLI**:
   ```bash
   curl -sSL install.astronomer.io | sudo bash -s
   ```

3. **Initialize project**:
   ```bash
   astro dev init
   ```

4. **Deploy DAGs**:
   ```bash
   astro deploy
   ```

5. **GitHub Integration**:
   - Add `ASTRONOMER_API_KEY` to GitHub Secrets
   - The workflow `.github/workflows/deploy-to-airflow.yml` handles deployment

---

### Option 3: Google Cloud Composer

**Pros:**
- Fully managed
- Integrates with GCP services
- Auto-scaling
- High availability

**Cons:**
- GCP-specific
- Costs ~$300/month minimum

**Setup:**

1. **Create Cloud Composer environment**:
   ```bash
   gcloud composer environments create economic-dashboard \
       --location us-central1 \
       --python-version 3
   ```

2. **Get DAGs bucket name**:
   ```bash
   gcloud composer environments describe economic-dashboard \
       --location us-central1 \
       --format="get(config.dagGcsPrefix)"
   ```

3. **Configure GitHub Secrets**:
   - `GCP_PROJECT`: Your GCP project ID
   - `GCP_COMPOSER_BUCKET`: Your Composer bucket
   - `GCP_SERVICE_ACCOUNT_KEY`: Service account JSON key

4. **Deploy**:
   The workflow automatically syncs DAGs to Cloud Composer bucket

---

### Option 4: GitHub Actions Only (Simplest)

**Pros:**
- No Airflow infrastructure needed
- Completely free
- Already implemented
- Easy to maintain

**Cons:**
- Less flexible than Airflow
- No complex dependencies
- No Airflow UI

**This is already set up!** Just use `.github/workflows/data-refresh.yml`

---

## Workflows Created

### 1. `trigger-airflow-dag.yml`
Triggers an Airflow DAG via REST API:
```bash
# Manual trigger from GitHub UI:
# Actions → Trigger Airflow DAG → Run workflow

# Automatic: Runs daily at 6 AM UTC
```

### 2. `deploy-to-airflow.yml`
Deploys DAG files to Airflow server:
```bash
# Triggers when you push to airflow/dags/
git add airflow/dags/economic_data_refresh_dag.py
git commit -m "Update DAG"
git push
```

### 3. `data-refresh.yml` (Already exists)
Pure GitHub Actions solution - no Airflow needed!

---

## Recommended Approach

### For Most Users: Use GitHub Actions Only ✅
- Already implemented in `.github/workflows/data-refresh.yml`
- No additional infrastructure
- Free and reliable
- Perfect for daily data refresh

### For Advanced Users: Self-Hosted Airflow + GitHub
If you need:
- Complex DAG dependencies
- Advanced scheduling
- Task monitoring and retry logic
- Multiple data pipelines

Then use Option 1 (Self-Hosted Airflow + GitHub Triggers)

---

## Setup Instructions for Self-Hosted Airflow + GitHub

### Step 1: Install Airflow on a Server

**Using Docker (Recommended):**
```bash
# Download Docker Compose file
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.7.0/docker-compose.yaml'

# Create directories
mkdir -p ./dags ./logs ./plugins ./config

# Set Airflow user
echo -e "AIRFLOW_UID=$(id -u)" > .env

# Initialize database
docker-compose up airflow-init

# Start Airflow
docker-compose up -d
```

**Access Airflow UI:** http://localhost:8080 (username: `airflow`, password: `airflow`)

### Step 2: Configure Airflow API

Edit `airflow.cfg` or set environment variable:
```bash
export AIRFLOW__API__AUTH_BACKEND=airflow.api.auth.backend.basic_auth
```

Restart Airflow:
```bash
docker-compose restart
```

### Step 3: Deploy Your DAG

Copy the DAG file:
```bash
cp airflow/dags/economic_data_refresh_dag.py ./dags/
```

Airflow will automatically detect it within ~30 seconds.

### Step 4: Configure GitHub Secrets

1. Go to your GitHub repo
2. Settings → Secrets and variables → Actions
3. Add these secrets:
   - `AIRFLOW_URL`: `http://your-server-ip:8080`
   - `AIRFLOW_USERNAME`: `airflow`
   - `AIRFLOW_PASSWORD`: `airflow`

### Step 5: Test the Integration

**Manual trigger from GitHub:**
1. Go to Actions tab
2. Click "Trigger Airflow DAG"
3. Click "Run workflow"
4. Check the logs

**Verify in Airflow:**
1. Open Airflow UI
2. Check "DAG Runs"
3. View task logs

### Step 6: Enable Daily Schedule

The workflow is already configured to run daily at 6 AM UTC.
Just enable the workflow and it will run automatically!

---

## Triggering DAGs Programmatically

### From GitHub Actions (Already Configured)
```yaml
- name: Trigger Airflow DAG
  run: |
    curl -X POST \
      "${AIRFLOW_URL}/api/v1/dags/economic_dashboard_data_refresh/dagRuns" \
      -H "Content-Type: application/json" \
      -u "${AIRFLOW_USERNAME}:${AIRFLOW_PASSWORD}" \
      -d '{"conf": {}}'
```

### From Command Line
```bash
curl -X POST \
  "http://localhost:8080/api/v1/dags/economic_dashboard_data_refresh/dagRuns" \
  -H "Content-Type: application/json" \
  -u "airflow:airflow" \
  -d '{"conf": {"test": true}}'
```

### From Python
```python
import requests
from requests.auth import HTTPBasicAuth

response = requests.post(
    "http://localhost:8080/api/v1/dags/economic_dashboard_data_refresh/dagRuns",
    auth=HTTPBasicAuth("airflow", "airflow"),
    json={"conf": {}}
)
print(response.json())
```

---

## Monitoring and Alerts

### Airflow UI
- View DAG runs: http://your-airflow:8080/dags
- Task logs: Click on task → View Log
- Gantt chart: Visual timeline of execution

### GitHub Actions
- View workflow runs: Actions tab
- See summaries in workflow output
- Check artifacts for data backups

### Email Alerts (Optional)
Configure in `airflow.cfg`:
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

Update DAG:
```python
default_args = {
    'email': ['your-email@gmail.com'],
    'email_on_failure': True,
    'email_on_retry': False,
}
```

---

## Troubleshooting

### Airflow API not accessible
```bash
# Check if API is enabled
docker-compose exec airflow-webserver cat /opt/airflow/airflow.cfg | grep auth_backend

# Should show: auth_backend = airflow.api.auth.backend.basic_auth
```

### DAG not showing up
```bash
# Check for syntax errors
python -m py_compile airflow/dags/economic_data_refresh_dag.py

# Check Airflow logs
docker-compose logs airflow-scheduler
```

### GitHub Actions can't reach Airflow
- Ensure Airflow is publicly accessible (or use VPN/tunnel)
- Check firewall rules allow port 8080
- Verify AIRFLOW_URL in GitHub Secrets

### Authentication failed
```bash
# Test credentials
curl -u "airflow:airflow" http://localhost:8080/api/v1/dags
```

---

## Cost Comparison

| Solution | Monthly Cost | Maintenance | Flexibility |
|----------|-------------|-------------|-------------|
| GitHub Actions Only | **$0** | ⭐ Low | ⭐⭐ Medium |
| Self-Hosted Airflow | **$5-50** | ⭐⭐ Medium | ⭐⭐⭐ High |
| Astronomer | **$110+** | ⭐ Low | ⭐⭐⭐ High |
| Cloud Composer | **$300+** | ⭐ Low | ⭐⭐⭐ High |

---

## Recommendation

**For your Economic Dashboard:**

✅ **Start with GitHub Actions Only** (`.github/workflows/data-refresh.yml`)
- It's already implemented
- Free and reliable
- Sufficient for daily data refresh

⚡ **Consider Airflow later if you need:**
- Multiple dependent pipelines
- Complex scheduling (hourly, event-driven)
- Advanced monitoring and alerting
- Task retries with exponential backoff

---

## Next Steps

1. **If using GitHub Actions only (recommended):**
   ```bash
   # Test the setup
   python scripts/test_refresh_setup.py
   
   # Enable the workflow
   # It's already configured - just push to GitHub!
   ```

2. **If using Airflow + GitHub:**
   ```bash
   # Set up Airflow (Docker)
   curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.7.0/docker-compose.yaml'
   docker-compose up -d
   
   # Deploy DAG
   cp airflow/dags/economic_data_refresh_dag.py ./dags/
   
   # Configure GitHub Secrets
   # Then trigger from GitHub Actions!
   ```

## Support

- Airflow Documentation: https://airflow.apache.org/docs/
- GitHub Actions: https://docs.github.com/en/actions
- Questions? Open an issue on GitHub
