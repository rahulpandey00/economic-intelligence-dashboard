<div align="center">

# 📊 Economic Dashboard

### Professional-Grade Financial Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![FRED API](https://img.shields.io/badge/FRED-API-00529B?style=for-the-badge)](https://fred.stlouisfed.org/)

**A comprehensive, real-time economic intelligence platform for tracking US macroeconomic indicators, market performance, and financial trends.**

[Features](#-features) • [Quick Start](#-quick-start) • [Documentation](#-documentation) • [Contributing](#-contributing)

---

</div>

## 🎯 Overview

The **Economic Dashboard** is an enterprise-grade analytical platform designed for financial professionals, economists, and data enthusiasts. It provides real-time access to over **60+ economic indicators** sourced from the Federal Reserve Economic Data (FRED) and Yahoo Finance, presented through an intuitive, modern interface.

### Why Economic Dashboard?

| Feature | Benefit |
|---------|---------|
| 📈 **Real-Time Data** | Live economic indicators updated automatically |
| 🎨 **Modern UI/UX** | Professional dark theme with responsive design |
| 🔒 **Secure** | Encrypted API key storage with industry standards |
| ⚡ **High Performance** | Intelligent caching for lightning-fast load times |
| 📱 **Responsive** | Works seamlessly across desktop and tablet |

---

## ✨ Features

### Homepage - Global Overview
- **Key Economic Indicators**: Real-time metrics for:
  - US GDP Growth (Quarterly % Change)
  - US Inflation (CPI % Change YoY)
  - US Federal Funds Rate
  - WTI Crude Oil Price
  - Gold Price
- **Interactive World GDP Map**: Visualize global GDP growth patterns
- **S&P 500 Performance Chart**: 5-year historical trend analysis
- **API Key Status**: Real-time indicator of authenticated access

### Economic Indicators Deep Dive
- **Multi-Country Comparison**: Compare economic metrics across major economies
- **Flexible Metric Selection**: Choose from GDP Growth, Inflation (CPI), or Unemployment Rate
- **Custom Date Ranges**: Filter data for specific time periods
- **Interactive Visualizations**: Dynamic charts with hover details and tooltips
- **Summary Statistics**: View latest values and period averages

### Financial Markets Deep Dive
- **Market Indices Analysis**:
  - Track S&P 500, NASDAQ, FTSE 100, Nikkei 225, and more
  - Normalized performance comparison
  - Customizable time periods
  
- **US Treasury Yield Curve**:
  - Historical 10-Year and 2-Year Treasury yields
  - Yield curve spread analysis with inversion detection
  - Visual indicators for recession signals
  
- **Market Volatility (VIX)**:
  - 3-year VIX trend analysis
  - Real-time volatility gauge with color-coded risk levels
  - Statistical summaries (average, min, max)

### 📄 SEC EDGAR Data Explorer (NEW)
- **Company Financials**: Access XBRL financial statement data via SEC's Company Facts API
- **SEC Filings Browser**: View and analyze recent 10-K, 10-Q, 8-K, and other filings
- **Institutional Holdings**: Track Form 13F holdings from institutional investment managers
- **Financial Statement Data Sets**: Download quarterly FSDS data for bulk analysis
- **CIK Lookup**: Search companies by ticker symbol or CIK number
- **Key Metrics Visualization**: Charts for revenue, net income, and other financial trends

**Available SEC Datasets:**
- Financial Statement Data Sets (quarterly XBRL data from all filers)
- Company Facts API (real-time standardized financial data)
- Form 13F Holdings (institutional investor positions)
- Fails-to-Deliver Data (settlement failure records)
- Company Submissions (filing history and metadata)

### 🔑 API Key Management (NEW)
- **Secure Storage**: Encrypted API key storage using industry-standard encryption
- **Multiple Services**: Support for FRED, Yahoo Finance, Alpha Vantage, Quandl, and more
- **Visual Management**: User-friendly interface for adding, updating, and removing keys
- **Status Indicators**: Real-time display of configured services
- **Higher Limits**: Automatic use of API keys for better rate limits and reliability

### 🔄 Automated Data Refresh (NEW)
- **Daily Updates**: Automatic data refresh at 6 AM UTC via GitHub Actions or Apache Airflow
- **Centralized Caching**: All economic data stored in unified cache for fast access
- **Backup System**: CSV backups created daily for inspection and recovery
- **Manual Triggers**: Run data refresh on-demand when needed
- **Quality Validation**: Automated checks ensure data freshness and completeness

For detailed setup instructions, see [docs/AUTOMATED_DATA_REFRESH.md](docs/AUTOMATED_DATA_REFRESH.md)

## 🚀 Live Demo

*Coming soon: Streamlit Cloud deployment link*

## 🛠️ Installation & Setup

### Prerequisites

- **Python 3.10+** — [Download Python](https://python.org)
- **pip** — Python package manager (included with Python)
- **Git** — [Download Git](https://git-scm.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/rahulpandey00/Economic-Dashboard.git
cd Economic-Dashboard

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the dashboard
streamlit run app.py
```

The dashboard will automatically open at **http://localhost:8501**

### 🔐 API Configuration (Recommended)

For enhanced rate limits and reliability, configure your API keys:

```bash
# Quick setup with guided prompts
python quickstart_api_keys.py

# Or use the setup script
python setup_credentials.py
```

> **💡 Pro Tip:** API keys are encrypted using industry-standard encryption and stored securely.

---

## 📖 Documentation

### 📂 Project Architecture

```
Economic-Dashboard/
├── 📱 app.py                    # Main application entry point
├── 📁 pages/                    # Dashboard pages
│   ├── 1_GDP_and_Growth.py
│   ├── 2_Inflation_and_Prices.py
│   ├── 3_Employment_and_Wages.py
│   ├── 4_Consumer_and_Housing.py
│   ├── 5_Markets_and_Rates.py
│   ├── 6_API_Key_Management.py
│   ├── 7_Market_Indices.py
│   ├── 8_Stock_Technical_Analysis.py
│   └── 9_News_Sentiment.py
├── 📁 modules/                  # Core functionality
│   ├── data_loader.py           # Data fetching & caching
│   ├── technical_analysis.py    # TA indicators
│   ├── sentiment_analysis.py    # News sentiment
│   └── auth/                    # Authentication
├── 📁 .streamlit/               # Streamlit configuration
│   └── config.toml              # Theme & settings
├── 📁 docs/                     # Documentation
├── 📁 tests/                    # Test suite
└── 📁 data/                     # Cache & sample data
```

### 🎨 Theme Configuration

Customize the dashboard appearance in `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#0068c9"
backgroundColor = "#040f26"
secondaryBackgroundColor = "#081943"
textColor = "#ffffff"
font = "sans serif"
```

### 🧪 Testing

```bash
# Run full test suite
python test_locally.py

# Run pytest with verbose output
python -m pytest tests/ -v

# Run with coverage report
python -m pytest tests/ --cov=modules --cov=pages
```

### 🔌 Offline Mode

Enable offline mode for development or limited connectivity:

```bash
# Linux/macOS
export ECONOMIC_DASHBOARD_OFFLINE=true
streamlit run app.py

# Windows PowerShell
$env:ECONOMIC_DASHBOARD_OFFLINE="true"
streamlit run app.py

# Windows Command Prompt
set ECONOMIC_DASHBOARD_OFFLINE=true
streamlit run app.py
```

---

## 📊 Data Sources

| Source | Data Types | Update Frequency |
|--------|------------|------------------|
| **FRED** | GDP, CPI, Employment, Interest Rates | Daily |
| **Yahoo Finance** | Stock prices, Market indices | Real-time |
| **World Bank** | International GDP comparisons | Quarterly |

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### Development Workflow

We use a two-environment workflow with `dev` and `main` branches:

| Branch | Environment | Purpose |
|--------|-------------|---------|
| `dev` | Development | Active development, feature testing |
| `main` | Production | Stable, production-ready code |

1. **Fork** the repository
2. **Create** a feature branch from `dev` (`git checkout -b feature/amazing-feature dev`)
3. **Develop** and test your changes
4. **Commit** your changes (`git commit -m 'Add amazing feature'`)
5. **Push** to the branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request targeting the `dev` branch

Changes in `dev` are promoted to `main` (production) after thorough testing.

For more details, see [docs/ENVIRONMENTS.md](docs/ENVIRONMENTS.md).

### Local Development

```bash
# Set development environment
export DASHBOARD_ENV=development

# Run the app
streamlit run app.py
```

Please read our contributing guidelines and ensure tests pass before submitting.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 Author

<div align="center">

**Rahul Pandey**


</div>

---

## 🙏 Acknowledgments

- Federal Reserve Bank of St. Louis for FRED API
- Yahoo Finance for market data API
- U.S. Securities and Exchange Commission (SEC) for EDGAR API and financial datasets
- Streamlit team for the amazing framework
- Plotly for powerful visualization tools

[![FRED](https://img.shields.io/badge/Federal_Reserve-FRED_API-00529B?style=flat-square)](https://fred.stlouisfed.org/)
[![Yahoo Finance](https://img.shields.io/badge/Yahoo-Finance_API-6001D2?style=flat-square)](https://finance.yahoo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Framework-FF4B4B?style=flat-square&logo=streamlit)](https://streamlit.io/)
[![Plotly](https://img.shields.io/badge/Plotly-Visualizations-3F4F75?style=flat-square&logo=plotly)](https://plotly.com/)

</div>

---

<div align="center">

**Built with ❤️ for the financial community**

*Track • Analyze • Decide*

</div>
