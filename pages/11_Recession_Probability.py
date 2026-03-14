"""
Recession Probability Monitor

A comprehensive view of US recession probability using multiple economic indicators.
This page provides:
- Current recession probability with risk level assessment
- Individual indicator signals and their contributions
- Historical recession probability chart
- Key indicator visualizations
- Detailed explanations of methodology
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.data_loader import load_fred_data, load_yfinance_data
from modules.ml.recession_model import (
    RecessionProbabilityModel,
    get_recession_indicator_series,
    INDICATOR_WEIGHTS
)

st.set_page_config(
    page_title="Recession Probability Monitor",
    page_icon="📉",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .risk-gauge {
        text-align: center;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    .risk-low { background: linear-gradient(135deg, #1e8449 0%, #27ae60 100%); }
    .risk-moderate { background: linear-gradient(135deg, #b7950b 0%, #f1c40f 100%); }
    .risk-elevated { background: linear-gradient(135deg, #d68910 0%, #f39c12 100%); }
    .risk-high { background: linear-gradient(135deg, #922b21 0%, #e74c3c 100%); }
    
    .probability-number {
        font-size: 3.5rem;
        font-weight: 700;
        color: white;
        margin: 0;
    }
    .risk-label {
        font-size: 1.5rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .indicator-card {
        background: linear-gradient(135deg, #081943 0%, #0a1f4d 100%);
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 0.5rem;
    }
    .signal-bar {
        height: 8px;
        border-radius: 4px;
        background: #1a1a2e;
        margin-top: 0.5rem;
    }
    .signal-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

# Page Header
st.title("📉 Recession Probability Monitor")
st.markdown("""
**Real-time assessment of US recession risk using leading economic indicators**

This model combines multiple recession predictors including yield curve inversions, 
labor market trends, financial stress indicators, and economic activity measures.
""")

st.divider()


@st.cache_data(ttl=3600)
def load_recession_data():
    """Load all required data for recession probability calculation."""
    # Get FRED series for recession indicators
    series_ids = get_recession_indicator_series()
    
    # Load FRED data
    fred_data = load_fred_data(series_ids)
    
    # Load market data (S&P 500)
    market_tickers = {'S&P 500': '^GSPC'}
    market_data = load_yfinance_data(market_tickers, period='5y')
    
    sp500_data = market_data.get('S&P 500', pd.DataFrame())
    
    return fred_data, sp500_data


# Load data
with st.spinner("Loading economic indicators..."):
    try:
        fred_data, market_data = load_recession_data()
        data_loaded = not fred_data.empty
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        data_loaded = False
        fred_data = pd.DataFrame()
        market_data = pd.DataFrame()

if data_loaded:
    # Initialize model and calculate probability
    model = RecessionProbabilityModel()
    model.load_indicators_from_data(fred_data, market_data)
    
    try:
        result = model.calculate_recession_probability()
        probability = result['probability']
        risk_level = result['risk_level']
        signals = result['signals']
        details = result['details']
        
        # === MAIN PROBABILITY DISPLAY ===
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            risk_class = f"risk-{risk_level.lower()}"
            st.markdown(f"""
            <div class="risk-gauge {risk_class}">
                <p class="probability-number">{probability:.1%}</p>
                <p class="risk-label">{risk_level} Risk</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.caption(f"📅 Last Updated: {result['calculation_time'][:19]}")
        
        st.divider()
        
        # === INDICATOR SIGNALS ===
        st.subheader("📊 Indicator Signals")
        st.markdown("Each indicator contributes to the overall recession probability based on its historical predictive power.")
        
        # Create signal visualization
        signal_cols = st.columns(len(signals))
        
        # Get explanations
        explanations = model.get_indicator_explanations()
        
        # Display each signal
        for idx, (signal_name, signal_value) in enumerate(signals.items()):
            with signal_cols[idx]:
                # Format the signal name
                display_name = signal_name.replace('_signal', '').replace('_', ' ').title()
                weight = INDICATOR_WEIGHTS.get(signal_name, 0)
                
                # Determine color based on signal strength
                if signal_value >= 0.7:
                    color = '#e74c3c'  # Red
                elif signal_value >= 0.4:
                    color = '#f39c12'  # Orange
                elif signal_value >= 0.2:
                    color = '#f1c40f'  # Yellow
                else:
                    color = '#27ae60'  # Green
                
                st.markdown(f"""
                <div class="indicator-card">
                    <div style="font-weight: 600; color: #0068c9;">{display_name}</div>
                    <div style="font-size: 1.5rem; font-weight: 700; color: white;">{signal_value:.0%}</div>
                    <div style="font-size: 0.8rem; color: rgba(255,255,255,0.6);">Weight: {weight:.0%}</div>
                    <div class="signal-bar">
                        <div class="signal-fill" style="width: {signal_value * 100}%; background: {color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.divider()
        
        # === DETAILED BREAKDOWN ===
        st.subheader("🔍 Detailed Indicator Analysis")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📈 Yield Curve",
            "💼 Labor Market",
            "🏦 Financial Conditions",
            "📊 Economic Activity"
        ])
        
        with tab1:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Current Yield Curve Status")
                yc_details = details.get('yield_curve', {})
                
                if '10y2y_spread' in yc_details:
                    spread = yc_details['10y2y_spread']
                    is_inverted = yc_details.get('10y2y_inverted', False)
                    
                    st.metric(
                        "10Y-2Y Treasury Spread",
                        f"{spread:.2f}%",
                        delta="INVERTED" if is_inverted else "NORMAL",
                        delta_color="inverse" if is_inverted else "normal"
                    )
                
                if '10y3m_spread' in yc_details:
                    spread_3m = yc_details['10y3m_spread']
                    is_inverted_3m = yc_details.get('10y3m_inverted', False)
                    
                    st.metric(
                        "10Y-3M Treasury Spread",
                        f"{spread_3m:.2f}%",
                        delta="INVERTED" if is_inverted_3m else "NORMAL",
                        delta_color="inverse" if is_inverted_3m else "normal"
                    )
                
                if 'recent_inversion' in yc_details:
                    st.info(f"📌 Recent Inversion (18mo): {'Yes' if yc_details['recent_inversion'] else 'No'}")
            
            with col2:
                st.markdown("#### Yield Spread History")
                if 'yield_spread_10y2y' in fred_data.columns:
                    spread_data = fred_data['yield_spread_10y2y'].dropna()
                    recent_spread = spread_data[spread_data.index >= datetime.now() - timedelta(days=365*5)]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=recent_spread.index,
                        y=recent_spread.values,
                        mode='lines',
                        name='10Y-2Y Spread',
                        line=dict(color='#0068c9', width=2)
                    ))
                    fig.add_hline(y=0, line_dash="dash", line_color="red",
                                  annotation_text="Inversion Threshold")
                    fig.update_layout(
                        template='plotly_dark',
                        height=300,
                        margin=dict(l=0, r=0, t=10, b=0),
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown(explanations.get('yield_curve_signal', ''))
        
        with tab2:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Labor Market Indicators")
                labor_details = details.get('labor_market', {})
                
                if 'unemployment_rate' in labor_details:
                    unemp = labor_details['unemployment_rate']
                    unemp_change = labor_details.get('unemployment_change_12m', 0)
                    
                    st.metric(
                        "Unemployment Rate",
                        f"{unemp:.1f}%",
                        delta=f"{unemp_change:+.1f}% (12mo)",
                        delta_color="inverse"
                    )
                
                if 'sahm_indicator' in labor_details:
                    sahm = labor_details['sahm_indicator']
                    sahm_triggered = labor_details.get('sahm_triggered', False)
                    
                    st.metric(
                        "Sahm Rule Indicator",
                        f"{sahm:.2f}pp",
                        delta="TRIGGERED" if sahm_triggered else f"{0.5 - sahm:.2f}pp to trigger",
                        delta_color="inverse" if sahm_triggered else "normal"
                    )
                
                if 'initial_claims_4wk_avg' in labor_details:
                    claims = labor_details['initial_claims_4wk_avg']
                    claims_change = labor_details.get('claims_change_pct', 0)
                    
                    st.metric(
                        "Initial Claims (4wk avg)",
                        f"{claims:,.0f}",
                        delta=f"{claims_change:+.1f}% vs 12wk avg",
                        delta_color="inverse" if claims_change > 0 else "normal"
                    )
            
            with col2:
                st.markdown("#### Unemployment Rate History")
                if 'unemployment_rate' in fred_data.columns:
                    unemp_data = fred_data['unemployment_rate'].dropna()
                    recent_unemp = unemp_data[unemp_data.index >= datetime.now() - timedelta(days=365*5)]
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=recent_unemp.index,
                        y=recent_unemp.values,
                        mode='lines',
                        name='Unemployment Rate',
                        line=dict(color='#e74c3c', width=2)
                    ))
                    fig.update_layout(
                        template='plotly_dark',
                        height=300,
                        margin=dict(l=0, r=0, t=10, b=0),
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown(explanations.get('labor_market_signal', ''))
        
        with tab3:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Financial Stress Indicators")
                financial_details = details.get('financial_stress', {})
                
                if 'corporate_spread' in financial_details:
                    spread = financial_details['corporate_spread']
                    avg_spread = financial_details.get('avg_spread', 0)
                    z_score = financial_details.get('spread_zscore', 0)
                    
                    st.metric(
                        "Corporate Bond Spread (BAA)",
                        f"{spread:.2f}%",
                        delta=f"Z-score: {z_score:+.2f}",
                        delta_color="inverse" if z_score > 0 else "normal"
                    )
                
                if 'fed_funds_rate' in financial_details:
                    ff_rate = financial_details['fed_funds_rate']
                    rate_change = financial_details.get('rate_change_12m', 0)
                    
                    st.metric(
                        "Fed Funds Rate",
                        f"{ff_rate:.2f}%",
                        delta=f"{rate_change:+.2f}pp (12mo)",
                        delta_color="off"
                    )
            
            with col2:
                st.markdown("#### Credit Spread History")
                if 'corporate_spread' in fred_data.columns:
                    spread_data = fred_data['corporate_spread'].dropna()
                    recent_spread = spread_data[spread_data.index >= datetime.now() - timedelta(days=365*5)]
                    
                    if not recent_spread.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=recent_spread.index,
                            y=recent_spread.values,
                            mode='lines',
                            name='BAA Spread',
                            line=dict(color='#f39c12', width=2)
                        ))
                        fig.update_layout(
                            template='plotly_dark',
                            height=300,
                            margin=dict(l=0, r=0, t=10, b=0),
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Credit spread data not available")
            
            st.markdown("---")
            st.markdown(explanations.get('financial_stress_signal', ''))
        
        with tab4:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Economic Activity Indicators")
                activity_details = details.get('economic_activity', {})
                consumer_details = details.get('consumer', {})
                
                if 'gdp_growth' in activity_details:
                    gdp = activity_details['gdp_growth']
                    two_neg = activity_details.get('two_negative_quarters', False)
                    
                    st.metric(
                        "Real GDP Growth",
                        f"{gdp:.1f}%",
                        delta="2 negative quarters!" if two_neg else "Quarterly rate"
                    )
                
                if 'industrial_production_yoy' in activity_details:
                    ip_yoy = activity_details['industrial_production_yoy']
                    
                    st.metric(
                        "Industrial Production",
                        f"{ip_yoy:+.1f}%",
                        delta="YoY Change",
                        delta_color="inverse" if ip_yoy < 0 else "normal"
                    )
                
                if 'consumer_sentiment' in consumer_details:
                    sentiment = consumer_details['consumer_sentiment']
                    sentiment_change = consumer_details.get('sentiment_change_12m', 0)
                    
                    st.metric(
                        "Consumer Sentiment",
                        f"{sentiment:.1f}",
                        delta=f"{sentiment_change:+.1f} (12mo)",
                        delta_color="inverse" if sentiment_change < 0 else "normal"
                    )
            
            with col2:
                st.markdown("#### Consumer Sentiment History")
                if 'consumer_sentiment' in fred_data.columns:
                    sentiment_data = fred_data['consumer_sentiment'].dropna()
                    recent_sentiment = sentiment_data[sentiment_data.index >= datetime.now() - timedelta(days=365*5)]
                    
                    if not recent_sentiment.empty:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=recent_sentiment.index,
                            y=recent_sentiment.values,
                            mode='lines',
                            name='Consumer Sentiment',
                            line=dict(color='#27ae60', width=2)
                        ))
                        fig.add_hline(y=80, line_dash="dash", line_color="gray",
                                      annotation_text="Historical Avg")
                        fig.update_layout(
                            template='plotly_dark',
                            height=300,
                            margin=dict(l=0, r=0, t=10, b=0),
                            showlegend=False
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Consumer sentiment data not available")
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(explanations.get('economic_activity_signal', ''))
            with col2:
                st.markdown(explanations.get('consumer_signal', ''))
        
        st.divider()
        
        # === METHODOLOGY ===
        with st.expander("📚 Methodology & Disclaimer"):
            st.markdown("""
            ### How This Model Works
            
            The Recession Probability Model combines multiple leading economic indicators 
            that have historically predicted US recessions. Each indicator generates a signal 
            strength (0-100%) based on current conditions compared to historical patterns.
            
            #### Key Indicators & Weights:
            """)
            
            weights_df = pd.DataFrame([
                {'Indicator': k.replace('_signal', '').replace('_', ' ').title(), 
                 'Weight': f"{v:.0%}",
                 'Description': explanations.get(k, 'N/A')[:100] + '...'}
                for k, v in INDICATOR_WEIGHTS.items()
            ])
            st.dataframe(weights_df, use_container_width=True, hide_index=True)
            
            st.markdown("""
            #### Risk Levels:
            - **LOW (0-20%)**: Economy appears healthy with minimal recession signals
            - **MODERATE (20-40%)**: Some warning signs present, but not conclusive
            - **ELEVATED (40-70%)**: Multiple indicators suggest elevated recession risk
            - **HIGH (70-100%)**: Strong signals indicate high probability of recession
            
            #### Important Disclaimer:
            This model is for **educational and informational purposes only**. It should not 
            be used as the sole basis for investment decisions. Economic forecasting is 
            inherently uncertain, and past indicator performance does not guarantee future 
            predictive accuracy.
            
            **Data Sources:** Federal Reserve Economic Data (FRED), Yahoo Finance
            """)
    
    except Exception as e:
        st.error(f"Error calculating recession probability: {str(e)}")
        st.info("Please check that all required economic data is available.")

else:
    st.warning("""
    ⚠️ **Unable to load economic indicator data**
    
    This page requires access to FRED (Federal Reserve Economic Data) to calculate 
    recession probabilities. Please ensure:
    
    1. You have an internet connection
    2. FRED API is accessible
    3. Consider configuring a FRED API key for better rate limits
    
    Go to the **API Key Management** page to configure your credentials.
    """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 0.85rem;">
    <p>Recession Probability Model v1.6 | Data refreshed hourly</p>
    <p>Built with ❤️ using FRED Economic Data & Streamlit</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📉 Recession Monitor")
    st.markdown("""
    This page calculates the probability of a US recession using 
    multiple leading economic indicators.
    
    **Key Indicators:**
    - 📈 Yield Curve
    - 💼 Labor Market
    - 🏦 Financial Stress
    - 📊 Economic Activity
    - 🛒 Consumer Health
    - 🏠 Housing Market
    - 📉 Stock Market
    """)
    
    st.divider()
    
    st.markdown("### 📖 Quick Reference")
    st.markdown("""
    **Yield Curve Inversion:** When short-term rates exceed long-term rates, 
    signaling expected economic weakness.
    
    **Sahm Rule:** A recession indicator that triggers when unemployment rises 
    0.5% above its recent low.
    
    **Credit Spread:** The difference between corporate bond yields and Treasury 
    yields - wider spreads indicate stress.
    """)
    
    st.divider()
    
    if data_loaded:
        st.success("✅ Data loaded successfully")
        st.caption(f"Last data point: {fred_data.index[-1].strftime('%Y-%m-%d') if not fred_data.empty else 'N/A'}")
    else:
        st.error("❌ Data not available")
