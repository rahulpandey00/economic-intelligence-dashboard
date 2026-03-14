"""
Sector Rotation Monitor Dashboard
Track market rotation patterns across 11 S&P 500 sectors
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

# Import sector rotation detector
try:
    from modules.features import SectorRotationDetector
    DETECTOR_AVAILABLE = True
except ImportError as e:
    DETECTOR_AVAILABLE = False
    DETECTOR_ERROR = str(e)

# Page configuration
st.set_page_config(
    page_title="Sector Rotation Monitor",
    page_icon="🔄",
    layout="wide"
)

st.title("🔄 Sector Rotation Monitor")
st.markdown("### Track market leadership and sector rotation patterns")

if not DETECTOR_AVAILABLE:
    st.error(f"❌ Sector Rotation Detector not available: {DETECTOR_ERROR}")
    st.stop()

# Initialize detector
detector = SectorRotationDetector()

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Analysis Settings")
    
    lookback_days = st.selectbox(
        "Lookback Period",
        options=[10, 20, 30, 60, 90],
        index=2,
        help="Number of days for relative strength calculation"
    )
    
    st.divider()
    
    if st.button("🔄 Refresh Sector Data", use_container_width=True):
        st.cache_data.clear()
        st.success("Cache cleared! Data will refresh.")
    
    st.divider()
    
    st.subheader("📚 Rotation Patterns")
    
    with st.expander("🟢 Risk-On"):
        st.markdown("""
        **Offensive sectors outperforming**
        - Technology, Consumer Discretionary leading
        - Defensive sectors (Utilities, Staples) lagging
        - **Signal**: Bullish sentiment, growth preference
        """)
    
    with st.expander("🔴 Risk-Off"):
        st.markdown("""
        **Defensive sectors outperforming**
        - Utilities, Consumer Staples, Healthcare leading
        - Cyclical/Growth sectors lagging
        - **Signal**: Bearish sentiment, flight to safety
        """)
    
    with st.expander("🟠 Cyclical Recovery"):
        st.markdown("""
        **Cyclical sectors leading**
        - Energy, Materials, Industrials outperforming
        - **Signal**: Economic recovery, inflation expectations
        """)
    
    st.divider()
    
    st.subheader("📊 Sector Classifications")
    st.markdown("""
    **Offensive (Growth):**
    - Technology
    - Consumer Discretionary
    - Communication Services
    - Financials
    
    **Defensive (Stability):**
    - Utilities
    - Consumer Staples
    - Healthcare
    
    **Cyclical (Economy-Driven):**
    - Energy
    - Materials
    - Industrials
    - Real Estate
    """)

# Main content
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Rotation Dashboard",
    "🎯 Relative Strength",
    "📈 Momentum Analysis",
    "🔗 Sector Correlation"
])

# === TAB 1: ROTATION DASHBOARD ===
with tab1:
    st.header("Market Rotation Pattern Analysis")
    
    with st.spinner("Analyzing sector rotation patterns..."):
        rotation_pattern = detector.detect_rotation_pattern(days=lookback_days)
    
    if 'error' in rotation_pattern:
        st.error(f"❌ Error: {rotation_pattern['error']}")
    else:
        # Display rotation pattern
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            pattern_emoji = {
                'Risk-On': '🟢',
                'Risk-Off': '🔴',
                'Cyclical Recovery': '🟠',
                'Broadening Rally': '🟡',
                'Mixed/Divergent': '⚪'
            }
            
            st.markdown(f"""
            ### {pattern_emoji.get(rotation_pattern['pattern'], '⚪')} {rotation_pattern['pattern']}
            **Confidence**: {rotation_pattern['confidence']}
            
            {rotation_pattern['description']}
            """)
        
        with col2:
            st.metric(
                "Sector Breadth",
                f"{rotation_pattern['sector_breadth']['breadth_ratio']:.0%}",
                help=f"{rotation_pattern['sector_breadth']['outperforming']} of {rotation_pattern['sector_breadth']['total_sectors']} sectors outperforming"
            )
            st.metric(
                "Concentration",
                f"{rotation_pattern['concentration']:.3f}",
                help="Lower = more dispersed leadership"
            )
        
        with col3:
            st.metric(
                "Offensive Avg RS",
                f"{rotation_pattern['offensive_avg_rs']:+.2f}%"
            )
            st.metric(
                "Defensive Avg RS",
                f"{rotation_pattern['defensive_avg_rs']:+.2f}%"
            )
        
        st.divider()
        
        # Leading and lagging sectors
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Leading Sectors")
            leading = rotation_pattern.get('leading_sectors', [])
            
            for i, sector in enumerate(leading):
                st.markdown(f"""
                **{i+1}. {sector['sector']} ({sector['ticker']})**  
                Relative Strength: **{sector['relative_strength']:+.2f}%**
                """)
        
        with col2:
            st.subheader("📉 Lagging Sectors")
            lagging = rotation_pattern.get('lagging_sectors', [])
            
            for i, sector in enumerate(lagging):
                st.markdown(f"""
                **{i+1}. {sector['sector']} ({sector['ticker']})**  
                Relative Strength: **{sector['relative_strength']:+.2f}%**
                """)
        
        st.divider()
        
        # Sector classification performance
        st.subheader("Performance by Sector Classification")
        
        classification_data = pd.DataFrame({
            'Classification': ['Offensive', 'Defensive', 'Cyclical'],
            'Avg Relative Strength': [
                rotation_pattern['offensive_avg_rs'],
                rotation_pattern['defensive_avg_rs'],
                rotation_pattern['cyclical_avg_rs']
            ]
        })
        
        fig = px.bar(
            classification_data,
            x='Classification',
            y='Avg Relative Strength',
            color='Avg Relative Strength',
            color_continuous_scale='RdYlGn',
            color_continuous_midpoint=0,
            title=f"Relative Strength by Sector Type ({lookback_days}-Day)"
        )
        
        fig.add_hline(y=0, line_dash="dash", line_color="white", opacity=0.5)
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

# === TAB 2: RELATIVE STRENGTH ===
with tab2:
    st.header("Sector Relative Strength vs S&P 500")
    
    with st.spinner("Calculating relative strength for all sectors..."):
        rs_df = detector.calculate_relative_strength(days=lookback_days)
    
    if rs_df.empty:
        st.error("❌ Could not load sector data")
    else:
        # Relative strength heatmap/treemap
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Treemap of relative strength
            fig = px.treemap(
                rs_df,
                path=[px.Constant("S&P 500 Sectors"), 'classification', 'sector'],
                values=rs_df['relative_strength'].abs() + 1,  # Add 1 to avoid zeros
                color='relative_strength',
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,
                hover_data=['ticker', 'sector_return', 'momentum', 'trend']
            )
            
            fig.update_traces(
                texttemplate="<b>%{label}</b><br>%{color:+.2f}%",
                textfont=dict(size=14),
                hovertemplate="<b>%{label}</b><br>RS: %{color:+.2f}%<br>Sector Return: %{customdata[1]:+.2f}%<br>Trend: %{customdata[3]}<extra></extra>"
            )
            
            fig.update_layout(
                title=f"Sector Relative Strength Treemap ({lookback_days}-Day)",
                height=500,
                coloraxis_colorbar=dict(
                    title="Rel. Strength %",
                    ticksuffix="%"
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Top Performers:**")
            top_5 = rs_df.head(5)[['sector', 'relative_strength']]
            for _, row in top_5.iterrows():
                st.markdown(f"**{row['sector']}**: {row['relative_strength']:+.2f}%")
            
            st.divider()
            
            st.markdown("**Bottom Performers:**")
            bottom_5 = rs_df.tail(5)[['sector', 'relative_strength']]
            for _, row in bottom_5.iterrows():
                st.markdown(f"**{row['sector']}**: {row['relative_strength']:+.2f}%")
        
        st.divider()
        
        # Detailed table
        st.subheader("Complete Sector Performance Table")
        
        display_df = rs_df[['rs_rank', 'sector', 'ticker', 'sector_return', 'spy_return', 
                             'relative_strength', 'momentum', 'trend', 'volatility', 'classification']].copy()
        
        display_df.columns = ['Rank', 'Sector', 'Ticker', 'Return %', 'SPY Return %', 
                               'Rel. Strength %', 'Momentum %', 'Trend', 'Volatility %', 'Type']
        
        # Format numbers
        for col in ['Return %', 'SPY Return %', 'Rel. Strength %', 'Momentum %', 'Volatility %']:
            display_df[col] = display_df[col].round(2)
        
        # Color-code by relative strength
        def highlight_rs(row):
            rs = row['Rel. Strength %']
            if rs > 2:
                return ['background-color: #ccffcc'] * len(row)
            elif rs > 0:
                return ['background-color: #f0fff0'] * len(row)
            elif rs > -2:
                return ['background-color: #fff0f0'] * len(row)
            else:
                return ['background-color: #ffcccc'] * len(row)
        
        styled_df = display_df.style.apply(highlight_rs, axis=1)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)

# === TAB 3: MOMENTUM ANALYSIS ===
with tab3:
    st.header("Dual-Timeframe Momentum Analysis")
    
    st.markdown("""
    Compare short-term (10-day) vs long-term (50-day) momentum to identify:
    - **Accelerating**: Both timeframes positive (strong momentum)
    - **Reversing Up**: Short-term positive, long-term negative (potential turnaround)
    - **Weakening**: Short-term negative, long-term positive (losing momentum)
    - **Declining**: Both timeframes negative (weak momentum)
    """)
    
    with st.spinner("Calculating momentum scores..."):
        momentum_df = detector.get_sector_momentum_scores(short_days=10, long_days=50)
    
    if momentum_df.empty:
        st.error("❌ Could not load momentum data")
    else:
        # Momentum quadrant chart
        fig = px.scatter(
            momentum_df,
            x='long_term_momentum',
            y='short_term_momentum',
            color='classification',
            size=momentum_df['divergence'].abs() + 5,
            text='sector',
            title="Momentum Quadrant Analysis",
            labels={
                'long_term_momentum': '50-Day Momentum (%)',
                'short_term_momentum': '10-Day Momentum (%)'
            },
            color_discrete_map={
                'Offensive': '#4CAF50',
                'Defensive': '#2196F3',
                'Cyclical': '#FF9800'
            }
        )
        
        # Add quadrant lines
        fig.add_hline(y=0, line_dash="dash", line_color="gray")
        fig.add_vline(x=0, line_dash="dash", line_color="gray")
        
        # Add quadrant labels
        fig.add_annotation(x=5, y=5, text="Accelerating Up", showarrow=False, font=dict(size=12, color="green"))
        fig.add_annotation(x=-5, y=5, text="Reversing Up", showarrow=False, font=dict(size=12, color="orange"))
        fig.add_annotation(x=5, y=-5, text="Weakening", showarrow=False, font=dict(size=12, color="orange"))
        fig.add_annotation(x=-5, y=-5, text="Declining", showarrow=False, font=dict(size=12, color="red"))
        
        fig.update_traces(textposition='top center')
        fig.update_layout(height=600)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Momentum state summary
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Momentum State Breakdown")
            state_counts = momentum_df['momentum_state'].value_counts()
            
            fig = px.pie(
                values=state_counts.values,
                names=state_counts.index,
                title="Sectors by Momentum State",
                color_discrete_sequence=px.colors.sequential.RdYlGn
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Momentum Table")
            display_momentum = momentum_df[['sector', 'short_term_momentum', 'long_term_momentum', 
                                           'divergence', 'momentum_state']].copy()
            display_momentum.columns = ['Sector', '10-Day %', '50-Day %', 'Divergence %', 'State']
            
            for col in ['10-Day %', '50-Day %', 'Divergence %']:
                display_momentum[col] = display_momentum[col].round(2)
            
            st.dataframe(display_momentum, use_container_width=True, hide_index=True, height=400)

# === TAB 4: SECTOR CORRELATION ===
with tab4:
    st.header("Sector Correlation Matrix")
    
    st.markdown("""
    Correlation analysis reveals how sectors move together:
    - **High correlation** (>0.7): Sectors moving in tandem
    - **Low correlation** (<0.3): Independent sector behavior
    - **Negative correlation** (<0): Inverse relationship
    """)
    
    with st.spinner("Calculating sector correlations (90-day)..."):
        corr_matrix = detector.calculate_sector_correlation_matrix(days=90)
    
    if corr_matrix.empty:
        st.error("❌ Could not load correlation data")
    else:
        # Correlation heatmap
        fig = px.imshow(
            corr_matrix,
            labels=dict(color="Correlation"),
            x=corr_matrix.columns,
            y=corr_matrix.index,
            color_continuous_scale='RdYlGn',
            zmin=-1,
            zmax=1,
            aspect="auto"
        )
        
        fig.update_layout(
            title="90-Day Sector Return Correlation Matrix",
            height=700,
            xaxis_title="",
            yaxis_title=""
        )
        
        fig.update_xaxes(side="bottom", tickangle=45)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.divider()
        
        # Correlation insights
        st.subheader("Correlation Insights")
        
        # Find highest and lowest correlations
        # Set diagonal to NaN to exclude self-correlation
        corr_no_diag = corr_matrix.where(~np.eye(len(corr_matrix), dtype=bool))
        
        # Highest correlations
        corr_stacked = corr_no_diag.stack().sort_values(ascending=False)
        highest_pairs = corr_stacked.head(5)
        
        # Lowest correlations
        lowest_pairs = corr_stacked.tail(5)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Most Correlated Sector Pairs:**")
            for (sector1, sector2), corr in highest_pairs.items():
                st.markdown(f"- **{sector1}** ↔ **{sector2}**: {corr:.3f}")
        
        with col2:
            st.markdown("**Least Correlated Sector Pairs:**")
            for (sector1, sector2), corr in lowest_pairs.items():
                st.markdown(f"- **{sector1}** ↔ **{sector2}**: {corr:.3f}")

# Footer
st.divider()
st.markdown("""
**About Sector Rotation**

Sector rotation is the movement of investment capital from one industry sector to another as the economy moves through different phases of the business cycle. Understanding rotation patterns helps identify:

- **Market sentiment** (risk-on vs risk-off)
- **Economic cycle phase** (early, mid, late expansion or recession)
- **Investment opportunities** (sectors to overweight/underweight)

**11 SPDR Sector ETFs tracked:**  
XLK (Technology), XLV (Healthcare), XLF (Financials), XLY (Consumer Disc.), XLC (Communication),  
XLI (Industrials), XLP (Consumer Staples), XLE (Energy), XLU (Utilities), XLRE (Real Estate), XLB (Materials)

*Data source: Yahoo Finance. Relative Strength calculated vs SPY (S&P 500 ETF).*
""")
