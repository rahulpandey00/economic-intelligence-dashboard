"""
Market Indices Dashboard
Overview of major market indices with multiple views including heatmap.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from modules.data_loader import load_yfinance_data
from config_settings import is_offline_mode


def get_close_prices(df: pd.DataFrame, ticker: str) -> pd.Series:
    """
    Safely extract Close prices from DataFrame, handling both single and multi-level columns.
    
    Args:
        df: DataFrame from yfinance
        ticker: The ticker symbol
        
    Returns:
        Series of close prices or None if not found
    """
    try:
        # Handle simple case first (already flattened by data loader)
        if 'Close' in df.columns and not isinstance(df.columns, pd.MultiIndex):
            return df['Close']
        
        # Handle MultiIndex columns
        if isinstance(df.columns, pd.MultiIndex):
            # Try specific ticker column first
            close_col = ('Close', ticker)
            if close_col in df.columns:
                return df[close_col]
            # Fall back to just 'Close' level
            if 'Close' in df.columns.get_level_values(0):
                close_df = df['Close']
                if isinstance(close_df, pd.DataFrame):
                    return close_df.iloc[:, 0]
                return close_df
        
        return None
    except Exception:
        return None


# Page configuration
st.set_page_config(
    page_title="Market Indices",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Market Indices Dashboard")
st.markdown("### Real-time overview of major market indices worldwide")

# Define major indices
MAJOR_INDICES = {
    # US Indices
    'S&P 500': '^GSPC',
    'NASDAQ': '^IXIC',
    'Dow Jones': '^DJI',
    'Russell 2000': '^RUT',
    # International Indices
    'FTSE 100': '^FTSE',
    'DAX': '^GDAXI',
    'Nikkei 225': '^N225',
    'Hang Seng': '^HSI',
}

# Sector ETFs for heatmap
SECTOR_ETFS = {
    'Technology': 'XLK',
    'Healthcare': 'XLV',
    'Financials': 'XLF',
    'Consumer Disc.': 'XLY',
    'Communication': 'XLC',
    'Industrials': 'XLI',
    'Consumer Staples': 'XLP',
    'Energy': 'XLE',
    'Utilities': 'XLU',
    'Real Estate': 'XLRE',
    'Materials': 'XLB',
}

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Settings")
    
    time_period = st.selectbox(
        "Time Period",
        options=['1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y'],
        index=3,
        help="Select the time period for analysis"
    )
    
    st.divider()
    
    if is_offline_mode():
        st.info("🔌 **Offline Mode**: Using cached/sample data")
    else:
        st.success("🌐 **Online Mode**: Using live data")

# Create tabs for different views
tab_overview, tab_performance, tab_heatmap, tab_correlation = st.tabs([
    "📈 Overview", 
    "📊 Performance Comparison", 
    "🗺️ Sector Heatmap",
    "🔗 Correlation Matrix"
])

# ==================== OVERVIEW TAB ====================
with tab_overview:
    st.subheader("Major Market Indices")
    
    # Load index data
    with st.spinner("Loading market data..."):
        index_data = load_yfinance_data(MAJOR_INDICES, period=time_period)
    
    if index_data:
        # Create metrics row for US indices
        st.markdown("#### 🇺🇸 US Markets")
        us_indices = ['S&P 500', 'NASDAQ', 'Dow Jones', 'Russell 2000']
        cols = st.columns(4)
        
        for i, idx_name in enumerate(us_indices):
            if idx_name in index_data and not index_data[idx_name].empty:
                df = index_data[idx_name]
                close_prices = get_close_prices(df, MAJOR_INDICES[idx_name])
                
                if close_prices is not None and len(close_prices) > 0:
                    current_price = close_prices.iloc[-1]
                    prev_price = close_prices.iloc[0]
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    
                    with cols[i]:
                        st.metric(
                            label=idx_name,
                            value=f"{current_price:,.2f}",
                            delta=f"{pct_change:+.2f}%"
                        )
                else:
                    with cols[i]:
                        st.metric(label=idx_name, value="N/A")
            else:
                with cols[i]:
                    st.metric(label=idx_name, value="N/A")
        
        # International indices
        st.markdown("#### 🌍 International Markets")
        intl_indices = ['FTSE 100', 'DAX', 'Nikkei 225', 'Hang Seng']
        cols = st.columns(4)
        
        for i, idx_name in enumerate(intl_indices):
            if idx_name in index_data and not index_data[idx_name].empty:
                df = index_data[idx_name]
                close_prices = get_close_prices(df, MAJOR_INDICES[idx_name])
                
                if close_prices is not None and len(close_prices) > 0:
                    current_price = close_prices.iloc[-1]
                    prev_price = close_prices.iloc[0]
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    
                    with cols[i]:
                        st.metric(
                            label=idx_name,
                            value=f"{current_price:,.2f}",
                            delta=f"{pct_change:+.2f}%"
                        )
                else:
                    with cols[i]:
                        st.metric(label=idx_name, value="N/A")
            else:
                with cols[i]:
                    st.metric(label=idx_name, value="N/A")
        
        st.divider()
        
        # Price charts
        st.markdown("#### Index Price Charts")
        
        # Select indices to display
        selected_indices = st.multiselect(
            "Select indices to compare",
            options=list(MAJOR_INDICES.keys()),
            default=['S&P 500', 'NASDAQ']
        )
        
        if selected_indices:
            # Normalize prices to 100 for comparison
            fig = go.Figure()
            
            for idx_name in selected_indices:
                if idx_name in index_data and not index_data[idx_name].empty:
                    df = index_data[idx_name]
                    close_prices = get_close_prices(df, MAJOR_INDICES[idx_name])
                    
                    if close_prices is not None and len(close_prices) > 0:
                        # Normalize to 100
                        normalized = (close_prices / close_prices.iloc[0]) * 100
                        
                        fig.add_trace(go.Scatter(
                            x=df.index,
                            y=normalized,
                            mode='lines',
                            name=idx_name,
                            hovertemplate=f'{idx_name}<br>%{{y:.2f}}<extra></extra>'
                        ))
            
            fig.update_layout(
                title="Normalized Price Performance (Base = 100)",
                xaxis_title="Date",
                yaxis_title="Normalized Price",
                template='plotly_dark',
                height=500,
                hovermode='x unified',
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            
            # Add horizontal line at 100
            fig.add_hline(y=100, line_dash="dash", line_color="gray", opacity=0.5)
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Unable to load market data. Please try again later.")

# ==================== PERFORMANCE TAB ====================
with tab_performance:
    st.subheader("Performance Comparison")
    
    # Load data for performance comparison
    with st.spinner("Loading performance data..."):
        perf_data = load_yfinance_data(MAJOR_INDICES, period='1y')
    
    if perf_data:
        # Calculate returns for different periods
        periods = {
            '1 Day': 1,
            '1 Week': 5,
            '1 Month': 21,
            '3 Months': 63,
            '6 Months': 126,
            'YTD': None,  # Special handling
            '1 Year': 252
        }
        
        performance_data = []
        
        for idx_name, ticker in MAJOR_INDICES.items():
            if idx_name in perf_data and not perf_data[idx_name].empty:
                df = perf_data[idx_name]
                close_prices = get_close_prices(df, ticker)
                
                if close_prices is not None and len(close_prices) > 0:
                    row = {'Index': idx_name}
                    current_price = close_prices.iloc[-1]
                    
                    for period_name, days in periods.items():
                        if period_name == 'YTD':
                            # Find the first trading day of the year
                            current_year = datetime.now().year
                            ytd_mask = close_prices.index.year == current_year
                            if ytd_mask.any():
                                start_price = close_prices[ytd_mask].iloc[0]
                                pct_return = ((current_price - start_price) / start_price) * 100
                                row[period_name] = pct_return
                            else:
                                row[period_name] = None
                        elif days and len(close_prices) > days:
                            start_price = close_prices.iloc[-days-1]
                            pct_return = ((current_price - start_price) / start_price) * 100
                            row[period_name] = pct_return
                        else:
                            row[period_name] = None
                    
                    performance_data.append(row)
        
        if performance_data:
            perf_df = pd.DataFrame(performance_data)
            perf_df = perf_df.set_index('Index')
            
            # Display as styled table
            st.markdown("#### Returns by Period (%)")
            
            def color_returns(val):
                if pd.isna(val):
                    return ''
                color = 'green' if val > 0 else 'red' if val < 0 else 'gray'
                return f'color: {color}'
            
            styled_df = perf_df.style.applymap(color_returns).format("{:.2f}%", na_rep="N/A")
            st.dataframe(styled_df, use_container_width=True)
            
            # Bar chart comparison
            st.markdown("#### Performance Bar Chart")
            period_to_show = st.selectbox(
                "Select period for comparison",
                options=['1 Day', '1 Week', '1 Month', '3 Months', '6 Months', 'YTD', '1 Year'],
                index=2
            )
            
            if period_to_show in perf_df.columns:
                chart_data = perf_df[period_to_show].dropna().sort_values(ascending=True)
                
                colors = ['green' if x > 0 else 'red' for x in chart_data.values]
                
                fig = go.Figure(go.Bar(
                    x=chart_data.values,
                    y=chart_data.index,
                    orientation='h',
                    marker_color=colors,
                    text=[f'{x:.2f}%' for x in chart_data.values],
                    textposition='outside'
                ))
                
                fig.update_layout(
                    title=f'{period_to_show} Performance',
                    xaxis_title='Return (%)',
                    yaxis_title='',
                    template='plotly_dark',
                    height=400,
                    showlegend=False
                )
                
                fig.add_vline(x=0, line_dash="solid", line_color="white", opacity=0.5)
                
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Unable to load performance data.")

# ==================== HEATMAP TAB ====================
with tab_heatmap:
    st.subheader("S&P 500 Sector Heatmap")
    st.markdown("Performance of major S&P 500 sectors")
    
    # Info about caching
    st.info("💡 Sector data is cached for 24 hours to avoid rate limiting. Refresh the page to force reload after cache expires.")
    
    # Time period for heatmap
    heatmap_period = st.selectbox(
        "Heatmap Period",
        options=['1d', '5d', '1mo', '3mo', 'YTD'],
        index=0,
        key='heatmap_period'
    )
    
    # Load sector ETF data
    with st.spinner("Loading sector data (may use cached data if recently fetched)..."):
        sector_data = load_yfinance_data(SECTOR_ETFS, period='1y')
    
    if sector_data and len(sector_data) > 0:
        sector_returns = {}
        
        for sector, ticker in SECTOR_ETFS.items():
            if sector in sector_data and not sector_data[sector].empty:
                df = sector_data[sector]
                
                # Handle MultiIndex columns
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                
                close_prices = get_close_prices(df, ticker)
                
                if close_prices is not None and len(close_prices) > 0:
                    current_price = close_prices.iloc[-1]
                    
                    if heatmap_period == '1d' and len(close_prices) > 1:
                        start_price = close_prices.iloc[-2]
                    elif heatmap_period == '5d' and len(close_prices) > 5:
                        start_price = close_prices.iloc[-6]
                    elif heatmap_period == '1mo' and len(close_prices) > 21:
                        start_price = close_prices.iloc[-22]
                    elif heatmap_period == '3mo' and len(close_prices) > 63:
                        start_price = close_prices.iloc[-64]
                    elif heatmap_period == 'YTD':
                        current_year = datetime.now().year
                        ytd_mask = close_prices.index.year == current_year
                        if ytd_mask.any():
                            start_price = close_prices[ytd_mask].iloc[0]
                        else:
                            start_price = close_prices.iloc[0]
                    else:
                        start_price = close_prices.iloc[0]
                    
                    pct_return = ((current_price - start_price) / start_price) * 100
                    sector_returns[sector] = pct_return
        
        if sector_returns:
            # Create treemap-style heatmap
            sectors = list(sector_returns.keys())
            returns = list(sector_returns.values())
            
            # Create a grid layout for the heatmap
            cols_per_row = 4
            num_rows = (len(sectors) + cols_per_row - 1) // cols_per_row
            
            # Sort by returns
            sorted_data = sorted(zip(sectors, returns), key=lambda x: x[1], reverse=True)
            
            # Create heatmap using plotly
            fig = go.Figure()
            
            # Create treemap
            fig = px.treemap(
                names=[s for s, _ in sorted_data],
                parents=["" for _ in sorted_data],
                values=[abs(r) + 1 for _, r in sorted_data],  # Size based on magnitude
                color=[r for _, r in sorted_data],
                color_continuous_scale='RdYlGn',
                color_continuous_midpoint=0,
            )
            
            # Update text to show sector name and return
            fig.update_traces(
                texttemplate="<b>%{label}</b><br>%{color:.2f}%",
                textfont=dict(size=14),
                hovertemplate="<b>%{label}</b><br>Return: %{color:.2f}%<extra></extra>"
            )
            
            fig.update_layout(
                title=f"Sector Performance ({heatmap_period})",
                template='plotly_dark',
                height=500,
                coloraxis_colorbar=dict(
                    title="Return %",
                    ticksuffix="%"
                )
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Also show as bar chart
            st.markdown("#### Sector Performance Ranking")
            
            fig_bar = go.Figure(go.Bar(
                x=[r for _, r in sorted_data],
                y=[s for s, _ in sorted_data],
                orientation='h',
                marker_color=['green' if r > 0 else 'red' for _, r in sorted_data],
                text=[f'{r:.2f}%' for _, r in sorted_data],
                textposition='outside'
            ))
            
            fig_bar.update_layout(
                xaxis_title='Return (%)',
                yaxis_title='',
                template='plotly_dark',
                height=450,
                showlegend=False
            )
            
            fig_bar.add_vline(x=0, line_dash="solid", line_color="white", opacity=0.5)
            
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.warning("No sector data available. This may be due to market hours or data provider issues.")
    else:
        st.warning("Unable to load sector data. Please check your connection or try again later.")

# ==================== CORRELATION TAB ====================
with tab_correlation:
    st.subheader("Index Correlation Matrix")
    st.markdown("Correlation between major indices based on daily returns")
    
    # Load data for correlation
    with st.spinner("Loading correlation data..."):
        corr_data = load_yfinance_data(MAJOR_INDICES, period='1y')
    
    if corr_data:
        # Build returns dataframe
        returns_df = pd.DataFrame()
        
        for idx_name, ticker in MAJOR_INDICES.items():
            if idx_name in corr_data and not corr_data[idx_name].empty:
                df = corr_data[idx_name]
                close_prices = get_close_prices(df, ticker)
                
                if close_prices is not None:
                    returns_df[idx_name] = close_prices.pct_change()
        
        if not returns_df.empty:
            # Calculate correlation matrix
            corr_matrix = returns_df.corr()
            
            # Create heatmap
            fig = px.imshow(
                corr_matrix,
                x=corr_matrix.columns,
                y=corr_matrix.index,
                color_continuous_scale='RdBu_r',
                zmin=-1,
                zmax=1,
                aspect='auto'
            )
            
            # Add correlation values as text
            for i, row in enumerate(corr_matrix.index):
                for j, col in enumerate(corr_matrix.columns):
                    fig.add_annotation(
                        x=col,
                        y=row,
                        text=f"{corr_matrix.loc[row, col]:.2f}",
                        showarrow=False,
                        font=dict(color='white' if abs(corr_matrix.loc[row, col]) > 0.5 else 'black')
                    )
            
            fig.update_layout(
                title="Daily Returns Correlation (1 Year)",
                template='plotly_dark',
                height=500,
                coloraxis_colorbar=dict(title="Correlation")
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Insights
            st.markdown("#### Key Insights")
            
            # Find highest and lowest correlations (excluding self-correlation)
            corr_pairs = []
            for i, idx1 in enumerate(corr_matrix.index):
                for j, idx2 in enumerate(corr_matrix.columns):
                    if i < j:  # Only upper triangle
                        corr_pairs.append((idx1, idx2, corr_matrix.loc[idx1, idx2]))
            
            corr_pairs.sort(key=lambda x: x[2], reverse=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Most Correlated Pairs:**")
                for pair in corr_pairs[:3]:
                    st.write(f"• {pair[0]} & {pair[1]}: {pair[2]:.3f}")
            
            with col2:
                st.markdown("**Least Correlated Pairs:**")
                for pair in corr_pairs[-3:]:
                    st.write(f"• {pair[0]} & {pair[1]}: {pair[2]:.3f}")
    else:
        st.warning("Unable to load correlation data.")

# Footer
st.divider()
st.markdown("""
**Data Sources:**
- Market data provided by Yahoo Finance
- Sector ETFs: SPDR Select Sector funds

**Note:** All performance figures are calculated based on closing prices. Past performance does not guarantee future results.
""")
