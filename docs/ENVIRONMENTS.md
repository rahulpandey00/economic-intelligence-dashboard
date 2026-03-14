# Environment Configuration

This project supports multiple environments to enable a proper development workflow.

## Environments

### Production (main branch)
- **Branch:** `main`
- **Environment Variable:** `DASHBOARD_ENV=production`
- **Purpose:** Stable, production-ready code
- **Deployment:** Automatically deployed to production on merge

### Development (dev branch)
- **Branch:** `dev`
- **Environment Variable:** `DASHBOARD_ENV=development`
- **Purpose:** Active development and testing of new features
- **Deployment:** Deployed to development/staging environment

## Environment-Specific Settings

The environments have different configurations:

| Setting | Development | Production |
|---------|-------------|------------|
| Debug Mode | Enabled | Disabled |
| Log Level | DEBUG | WARNING |
| Cache Expiry | 1 hour | 24 hours |
| Rate Limit Delay | 0.1s | 0.5s |
| Experimental Features | Enabled | Disabled |
| API Timeout | 60s | 30s |
| Max Retries | 1 | 3 |

## Workflow

### Development Flow

1. **Create feature branch** from `dev`:
   ```bash
   git checkout dev
   git pull origin dev
   git checkout -b feature/my-feature
   ```

2. **Develop and test** your changes locally:
   ```bash
   export DASHBOARD_ENV=development
   streamlit run app.py
   ```

3. **Push and create PR** to `dev`:
   ```bash
   git push origin feature/my-feature
   # Create PR targeting 'dev' branch
   ```

4. **Merge to dev** after review and CI passes

5. **Test in dev environment** to validate changes

### Promotion to Production

1. **Trigger promotion workflow**:
   - Go to Actions → "Promote Dev to Production"
   - Click "Run workflow"
   - Type "PROMOTE" to confirm
   - Click "Run workflow"

2. **Review the generated PR** from dev to main

3. **Merge the PR** after approval

4. **Automatic deployment** to production occurs

### Hotfixes

For urgent fixes to production:

1. **Create hotfix branch** from `main`:
   ```bash
   git checkout main
   git checkout -b hotfix/critical-fix
   ```

2. **Apply fix and merge** directly to `main`

3. **Sync workflow runs automatically** to create a PR syncing changes back to `dev`

## GitHub Actions Workflows

### CI/CD Pipeline (`ci-cd.yml`)
- Runs on pushes and PRs to both `main` and `dev`
- Executes tests and code quality checks
- Deploys based on branch:
  - `dev` → Development environment
  - `main` → Production environment

### Promote Dev to Production (`promote-dev-to-prod.yml`)
- Manual workflow to promote dev changes to production
- Requires confirmation ("PROMOTE")
- Runs full test suite before creating PR
- Creates PR for final review

### Sync Main to Dev (`sync-main-to-dev.yml`)
- Runs automatically when main is updated
- Creates PR to sync hotfixes back to dev
- Keeps dev in sync with production

### Data Refresh (`data-refresh.yml`)
- Supports environment selection via workflow dispatch
- Auto-detects environment based on branch

## Configuration Files

### Streamlit Configs
- `.streamlit/environments/config.dev.toml` - Development config
- `.streamlit/environments/config.prod.toml` - Production config

### Environment Module
- `environments/config.py` - Python environment configuration
- `environments/__init__.py` - Module exports

## Local Development

To run in development mode:
```bash
export DASHBOARD_ENV=development
streamlit run app.py
```

To run in production mode locally:
```bash
export DASHBOARD_ENV=production
streamlit run app.py
```

## Setting Up a New Clone

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set environment: `export DASHBOARD_ENV=development`
4. Run the app: `streamlit run app.py`
