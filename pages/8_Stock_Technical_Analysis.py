"""
Stock Technical Analysis Dashboard
Daily-level technical analysis with Elliott Wave theory for top active stocks.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from modules.data_loader import load_yfinance_data
from modules.technical_analysis import (
    calculate_sma,
    calculate_ema,
    calculate_rsi,
    calculate_macd,
    calculate_bollinger_bands,
    calculate_stochastic,
    detect_elliott_waves,
    validate_elliott_impulse,
    get_fibonacci_retracements,
    get_fibonacci_extensions,
    identify_support_resistance,
    get_trend_strength
)
from config_settings import is_offline_mode

# Page configuration
st.set_page_config(
    page_title="Stock Technical Analysis",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Stock Technical Analysis")
st.markdown("### Daily technical analysis with Elliott Wave theory")

# Top 20 Most Active Stocks for 2025
TOP_20_STOCKS = {
    'NVDA': 'NVIDIA Corporation',
    'TSLA': 'Tesla, Inc.',
    'AAPL': 'Apple Inc.',
    'AMD': 'Advanced Micro Devices',
    'AMZN': 'Amazon.com Inc.',
    'MSFT': 'Microsoft Corporation',
    'META': 'Meta Platforms Inc.',
    'GOOGL': 'Alphabet Inc.',
    'PLTR': 'Palantir Technologies',
    'SOFI': 'SoFi Technologies',
    'NIO': 'NIO Inc.',
    'BAC': 'Bank of America',
    'INTC': 'Intel Corporation',
    'F': 'Ford Motor Company',
    'T': 'AT&T Inc.',
    'SMCI': 'Super Micro Computer',
    'MARA': 'Marathon Digital Holdings',
    'RIVN': 'Rivian Automotive',
    'COIN': 'Coinbase Global',
    'MU': 'Micron Technology'
}

# Sidebar controls
with st.sidebar:
    st.header("⚙️ Analysis Settings")
    
    # Stock selection
    selected_stock = st.selectbox(
        "Select Stock",
        options=list(TOP_20_STOCKS.keys()),
        format_func=lambda x: f"{x} - {TOP_20_STOCKS[x]}",
        index=0
    )
    
    st.divider()
    
    # Time period
    time_period = st.selectbox(
        "Time Period",
        options=['3mo', '6mo', '1y', '2y'],
        index=2,
        help="Historical data period for analysis"
    )
    
    st.divider()
    
    # Technical indicators
    st.subheader("📊 Technical Indicators")
    
    show_sma = st.checkbox("Simple Moving Averages", value=True)
    if show_sma:
        sma_periods = st.multiselect(
            "SMA Periods",
            options=[10, 20, 50, 100, 200],
            default=[20, 50, 200]
        )
    else:
        sma_periods = []
    
    show_ema = st.checkbox("Exponential Moving Averages", value=False)
    if show_ema:
        ema_periods = st.multiselect(
            "EMA Periods",
            options=[9, 12, 21, 26, 50],
            default=[12, 26]
        )
    else:
        ema_periods = []
    
    show_bb = st.checkbox("Bollinger Bands", value=True)
    show_volume = st.checkbox("Volume", value=True)
    
    st.divider()
    
    # Oscillators
    st.subheader("📉 Oscillators")
    show_rsi = st.checkbox("RSI (14)", value=True)
    show_macd = st.checkbox("MACD", value=True)
    show_stoch = st.checkbox("Stochastic", value=False)
    
    st.divider()
    
    # Elliott Wave settings
    st.subheader("🌊 Elliott Wave")
    show_elliott = st.checkbox("Show Elliott Waves", value=True)
    # Initialize with defaults
    wave_sensitivity = 15
    min_wave_pct = 0.03
    if show_elliott:
        wave_sensitivity = st.slider(
            "Wave Sensitivity",
            min_value=5,
            max_value=30,
            value=15,
            help="Higher = fewer waves detected"
        )
        min_wave_pct = st.slider(
            "Min Wave Size (%)",
            min_value=1.0,
            max_value=10.0,
            value=3.0,
            step=0.5
        ) / 100
    
    show_fibonacci = st.checkbox("Fibonacci Levels", value=True)
    show_support_resistance = st.checkbox("Support/Resistance", value=True)
    
    st.divider()
    
    if is_offline_mode():
        st.info("🔌 **Offline Mode**: Using cached/sample data")
    else:
        st.success("🌐 **Online Mode**: Live data (cached for 24 hours)")

# Main content area
st.info("💡 Stock data is cached for 24 hours to avoid rate limiting. Data refreshes automatically after cache expires.")

# Load stock data
with st.spinner(f"Loading {selected_stock} data (using cache if available)..."):
    stock_data = load_yfinance_data({selected_stock: selected_stock}, period=time_period)

if stock_data and selected_stock in stock_data and not stock_data[selected_stock].empty:
    df = stock_data[selected_stock].copy()
    
    # Handle multi-index columns from yfinance
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    
    # Ensure we have required columns
    required_cols = ['Open', 'High', 'Low', 'Close', 'Volume']
    if not all(col in df.columns for col in required_cols):
        st.error("Missing required price data columns")
        st.stop()
    
    # Pre-calculate Elliott Waves if enabled (to avoid duplicate calculation)
    waves = None
    if show_elliott:
        waves = detect_elliott_waves(df['Close'], window=wave_sensitivity, min_wave_pct=min_wave_pct)
    
    # Stock header with current price
    current_price = df['Close'].iloc[-1]
    prev_close = df['Close'].iloc[-2] if len(df) > 1 else current_price
    price_change = current_price - prev_close
    pct_change = (price_change / prev_close) * 100
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label=f"{selected_stock}",
            value=f"${current_price:.2f}",
            delta=f"{price_change:+.2f} ({pct_change:+.2f}%)"
        )
    
    with col2:
        st.metric("Day High", f"${df['High'].iloc[-1]:.2f}")
    
    with col3:
        st.metric("Day Low", f"${df['Low'].iloc[-1]:.2f}")
    
    with col4:
        st.metric("Volume", f"{df['Volume'].iloc[-1]:,.0f}")
    
    with col5:
        trend = get_trend_strength(df['Close'])
        st.metric("Trend", trend)
    
    st.divider()
    
    # Create main chart with subplots
    # Count number of subplot rows needed
    num_rows = 1  # Main price chart
    if show_volume:
        num_rows += 1
    if show_rsi:
        num_rows += 1
    if show_macd:
        num_rows += 1
    if show_stoch:
        num_rows += 1
    
    # Set row heights
    row_heights = [0.5]  # Main chart takes 50%
    remaining = 0.5
    extra_rows = num_rows - 1
    if extra_rows > 0:
        each_height = remaining / extra_rows
        row_heights.extend([each_height] * extra_rows)
    
    fig = make_subplots(
        rows=num_rows,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=row_heights,
        subplot_titles=None
    )
    
    current_row = 1
    
    # ==================== MAIN PRICE CHART ====================
    # Candlestick chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26a69a',
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Add SMAs
    sma_colors = ['#FFA500', '#00CED1', '#FF69B4', '#32CD32', '#9370DB']
    for i, period in enumerate(sma_periods):
        sma = calculate_sma(df['Close'], period)
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=sma,
                mode='lines',
                name=f'SMA {period}',
                line=dict(color=sma_colors[i % len(sma_colors)], width=1)
            ),
            row=1, col=1
        )
    
    # Add EMAs
    ema_colors = ['#FFD700', '#00FF7F', '#FF4500', '#1E90FF', '#FF1493']
    for i, period in enumerate(ema_periods):
        ema = calculate_ema(df['Close'], period)
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=ema,
                mode='lines',
                name=f'EMA {period}',
                line=dict(color=ema_colors[i % len(ema_colors)], width=1, dash='dash')
            ),
            row=1, col=1
        )
    
    # Add Bollinger Bands
    if show_bb:
        upper, middle, lower = calculate_bollinger_bands(df['Close'])
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=upper,
                mode='lines',
                name='BB Upper',
                line=dict(color='rgba(173, 216, 230, 0.7)', width=1)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=lower,
                mode='lines',
                name='BB Lower',
                line=dict(color='rgba(173, 216, 230, 0.7)', width=1),
                fill='tonexty',
                fillcolor='rgba(173, 216, 230, 0.1)'
            ),
            row=1, col=1
        )
    
    # Add Elliott Waves (use pre-calculated waves)
    if show_elliott and waves:
            # Draw wave lines
            wave_x = [df.index[w['index']] for w in waves if w['index'] < len(df.index)]
            wave_y = [w['price'] for w in waves if w['index'] < len(df.index)]
            
            fig.add_trace(
                go.Scatter(
                    x=wave_x,
                    y=wave_y,
                    mode='lines+markers',
                    name='Elliott Waves',
                    line=dict(color='yellow', width=2, dash='dot'),
                    marker=dict(size=10, symbol='diamond')
                ),
                row=1, col=1
            )
            
            # Add wave labels
            for wave in waves:
                if wave['index'] < len(df.index):
                    color = '#00FF00' if wave['wave_type'] == 'impulse' else '#FF6B6B'
                    fig.add_annotation(
                        x=df.index[wave['index']],
                        y=wave['price'],
                        text=wave['label'],
                        showarrow=True,
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=1,
                        arrowcolor=color,
                        font=dict(size=14, color=color, weight='bold'),
                        bgcolor='rgba(0,0,0,0.7)',
                        bordercolor=color,
                        borderwidth=1,
                        row=1, col=1
                    )
    
    # Add Fibonacci retracements
    if show_fibonacci and len(df) > 20:
        high_price = df['High'].max()
        low_price = df['Low'].min()
        fib_levels = get_fibonacci_retracements(high_price, low_price)
        
        fib_colors = ['rgba(255,255,255,0.3)', 'rgba(255,215,0,0.3)', 'rgba(0,255,0,0.3)',
                      'rgba(0,191,255,0.3)', 'rgba(255,0,255,0.3)', 'rgba(255,165,0,0.3)',
                      'rgba(255,255,255,0.3)']
        
        for i, (level, price) in enumerate(fib_levels.items()):
            fig.add_hline(
                y=price,
                line_dash="dash",
                line_color=fib_colors[i],
                annotation_text=f"Fib {level}: ${price:.2f}",
                annotation_position="left",
                row=1, col=1
            )
    
    # Add Support/Resistance levels
    if show_support_resistance:
        supports, resistances = identify_support_resistance(df['Close'], window=20, num_levels=3)
        
        for support in supports:
            fig.add_hline(
                y=support,
                line_dash="dot",
                line_color="green",
                line_width=1,
                annotation_text=f"S: ${support:.2f}",
                annotation_position="right",
                row=1, col=1
            )
        
        for resistance in resistances:
            fig.add_hline(
                y=resistance,
                line_dash="dot",
                line_color="red",
                line_width=1,
                annotation_text=f"R: ${resistance:.2f}",
                annotation_position="right",
                row=1, col=1
            )
    
    current_row += 1
    
    # ==================== VOLUME ====================
    if show_volume:
        colors = ['#26a69a' if df['Close'].iloc[i] >= df['Open'].iloc[i] else '#ef5350' 
                  for i in range(len(df))]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ),
            row=current_row, col=1
        )
        
        # Add volume moving average
        vol_ma = calculate_sma(df['Volume'], 20)
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=vol_ma,
                mode='lines',
                name='Vol MA(20)',
                line=dict(color='yellow', width=1)
            ),
            row=current_row, col=1
        )
        
        current_row += 1
    
    # ==================== RSI ====================
    if show_rsi:
        rsi = calculate_rsi(df['Close'])
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=rsi,
                mode='lines',
                name='RSI(14)',
                line=dict(color='#E040FB', width=1.5)
            ),
            row=current_row, col=1
        )
        
        # Overbought/Oversold lines
        fig.add_hline(y=70, line_dash="dash", line_color="red", line_width=1, row=current_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", line_width=1, row=current_row, col=1)
        fig.add_hline(y=50, line_dash="dot", line_color="gray", line_width=1, row=current_row, col=1)
        
        # Add RSI annotation
        current_rsi = rsi.iloc[-1]
        rsi_status = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
        fig.add_annotation(
            x=df.index[-1],
            y=current_rsi,
            text=f"RSI: {current_rsi:.1f} ({rsi_status})",
            showarrow=False,
            xanchor='left',
            font=dict(size=10),
            row=current_row, col=1
        )
        
        current_row += 1
    
    # ==================== MACD ====================
    if show_macd:
        macd_line, signal_line, histogram = calculate_macd(df['Close'])
        
        # Histogram
        colors = ['#26a69a' if h >= 0 else '#ef5350' for h in histogram]
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=histogram,
                name='MACD Histogram',
                marker_color=colors,
                opacity=0.7
            ),
            row=current_row, col=1
        )
        
        # MACD line
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=macd_line,
                mode='lines',
                name='MACD',
                line=dict(color='#2196F3', width=1.5)
            ),
            row=current_row, col=1
        )
        
        # Signal line
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=signal_line,
                mode='lines',
                name='Signal',
                line=dict(color='#FF9800', width=1.5)
            ),
            row=current_row, col=1
        )
        
        fig.add_hline(y=0, line_dash="solid", line_color="gray", line_width=1, row=current_row, col=1)
        
        current_row += 1
    
    # ==================== STOCHASTIC ====================
    if show_stoch:
        k_percent, d_percent = calculate_stochastic(df['High'], df['Low'], df['Close'])
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=k_percent,
                mode='lines',
                name='%K',
                line=dict(color='#2196F3', width=1.5)
            ),
            row=current_row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=df.index,
                y=d_percent,
                mode='lines',
                name='%D',
                line=dict(color='#FF9800', width=1.5)
            ),
            row=current_row, col=1
        )
        
        fig.add_hline(y=80, line_dash="dash", line_color="red", line_width=1, row=current_row, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", line_width=1, row=current_row, col=1)
    
    # Update layout
    fig.update_layout(
        title=f"{selected_stock} - {TOP_20_STOCKS[selected_stock]} | Technical Analysis",
        template='plotly_dark',
        height=800 + (100 * (num_rows - 1)),
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        hovermode='x unified'
    )
    
    # Update y-axes labels
    fig.update_yaxes(title_text="Price ($)", row=1, col=1)
    
    row_idx = 2
    if show_volume:
        fig.update_yaxes(title_text="Volume", row=row_idx, col=1)
        row_idx += 1
    if show_rsi:
        fig.update_yaxes(title_text="RSI", row=row_idx, col=1)
        row_idx += 1
    if show_macd:
        fig.update_yaxes(title_text="MACD", row=row_idx, col=1)
        row_idx += 1
    if show_stoch:
        fig.update_yaxes(title_text="Stoch", row=row_idx, col=1)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ==================== ELLIOTT WAVE ANALYSIS ====================
    if show_elliott:
        st.divider()
        st.subheader("🌊 Elliott Wave Analysis")
        
        # Use pre-calculated waves from earlier
        if waves:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Detected Wave Pattern")
                
                # Display wave summary
                impulse_waves = [w for w in waves if w['wave_type'] == 'impulse']
                corrective_waves = [w for w in waves if w['wave_type'] == 'corrective']
                
                st.write(f"**Impulse Waves Detected:** {len(impulse_waves)}")
                st.write(f"**Corrective Waves Detected:** {len(corrective_waves)}")
                
                # Wave details table
                wave_df = pd.DataFrame([
                    {
                        'Wave': w['label'],
                        'Type': w['wave_type'].capitalize(),
                        'Price': f"${w['price']:.2f}",
                        'Date': df.index[w['index']].strftime('%Y-%m-%d') if w['index'] < len(df.index) else 'N/A'
                    }
                    for w in waves if w['index'] < len(df.index)
                ])
                
                st.dataframe(wave_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.markdown("#### Wave Validation")
                
                is_valid, violations = validate_elliott_impulse(waves)
                
                if is_valid:
                    st.success("✅ Valid Elliott Wave impulse pattern detected!")
                else:
                    st.warning("⚠️ Pattern may not follow classic Elliott Wave rules:")
                    for violation in violations:
                        st.write(f"• {violation}")
                
                # Fibonacci projections
                if len(impulse_waves) >= 3:
                    st.markdown("#### Fibonacci Extension Targets")
                    
                    extensions = get_fibonacci_extensions(
                        impulse_waves[0]['price'],
                        impulse_waves[1]['price'],
                        impulse_waves[2]['price']
                    )
                    
                    for level, price in extensions.items():
                        st.write(f"**{level}:** ${price:.2f}")
        else:
            st.info("No clear Elliott Wave pattern detected with current sensitivity settings. Try adjusting the wave sensitivity or minimum wave size.")
    
    # ==================== TECHNICAL SUMMARY ====================
    st.divider()
    st.subheader("📊 Technical Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Moving Averages")
        
        sma_20 = calculate_sma(df['Close'], 20).iloc[-1]
        sma_50 = calculate_sma(df['Close'], 50).iloc[-1]
        sma_200 = calculate_sma(df['Close'], 200).iloc[-1] if len(df) >= 200 else None
        
        ma_signals = []
        
        if current_price > sma_20:
            ma_signals.append("Above SMA(20) ✅")
        else:
            ma_signals.append("Below SMA(20) ❌")
        
        if current_price > sma_50:
            ma_signals.append("Above SMA(50) ✅")
        else:
            ma_signals.append("Below SMA(50) ❌")
        
        if sma_200 is not None:
            if current_price > sma_200:
                ma_signals.append("Above SMA(200) ✅")
            else:
                ma_signals.append("Below SMA(200) ❌")
        
        for signal in ma_signals:
            st.write(f"• {signal}")
        
        # Golden/Death Cross
        if sma_200 is not None:
            if sma_50 > sma_200:
                st.success("🌟 Golden Cross (Bullish)")
            else:
                st.error("💀 Death Cross (Bearish)")
    
    with col2:
        st.markdown("#### Momentum Indicators")
        
        rsi_val = calculate_rsi(df['Close']).iloc[-1]
        macd_line_val, signal_line_val, _ = calculate_macd(df['Close'])
        macd_val = macd_line_val.iloc[-1]
        signal_val = signal_line_val.iloc[-1]
        
        # RSI interpretation
        if rsi_val > 70:
            st.write(f"• RSI({rsi_val:.1f}): Overbought ⚠️")
        elif rsi_val < 30:
            st.write(f"• RSI({rsi_val:.1f}): Oversold ⚠️")
        else:
            st.write(f"• RSI({rsi_val:.1f}): Neutral ✓")
        
        # MACD interpretation
        if macd_val > signal_val:
            st.write("• MACD: Bullish Crossover ✅")
        else:
            st.write("• MACD: Bearish Crossover ❌")
        
        if macd_val > 0:
            st.write("• MACD: Above Zero ✅")
        else:
            st.write("• MACD: Below Zero ❌")
    
    with col3:
        st.markdown("#### Price Action")
        
        # Bollinger Band position
        upper, middle, lower = calculate_bollinger_bands(df['Close'])
        
        if current_price > upper.iloc[-1]:
            st.write("• BB: Above Upper Band ⚠️")
        elif current_price < lower.iloc[-1]:
            st.write("• BB: Below Lower Band ⚠️")
        else:
            st.write("• BB: Within Bands ✓")
        
        # 52-week high/low
        high_52w = df['High'].max()
        low_52w = df['Low'].min()
        pct_from_high = ((current_price - high_52w) / high_52w) * 100
        pct_from_low = ((current_price - low_52w) / low_52w) * 100
        
        st.write(f"• {pct_from_high:.1f}% from period high")
        st.write(f"• +{pct_from_low:.1f}% from period low")
        
        # Overall signal
        bullish_signals = 0
        bearish_signals = 0
        
        if current_price > sma_20:
            bullish_signals += 1
        else:
            bearish_signals += 1
        if current_price > sma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1
        if 30 < rsi_val < 70:
            bullish_signals += 0.5
            bearish_signals += 0.5
        elif rsi_val > 50:
            bullish_signals += 1
        else:
            bearish_signals += 1
        if macd_val > signal_val:
            bullish_signals += 1
        else:
            bearish_signals += 1
        
        st.markdown("---")
        if bullish_signals > bearish_signals:
            st.success(f"📈 Overall: BULLISH ({bullish_signals:.0f}/{bullish_signals+bearish_signals:.0f})")
        elif bearish_signals > bullish_signals:
            st.error(f"📉 Overall: BEARISH ({bearish_signals:.0f}/{bullish_signals+bearish_signals:.0f})")
        else:
            st.info("↔️ Overall: NEUTRAL")

else:
    st.error(f"Unable to load data for {selected_stock}. Please try again later.")

# Footer
st.divider()
st.markdown("""
**Disclaimer:** This technical analysis is for educational purposes only and should not be considered as financial advice. 
Past performance does not guarantee future results. Always do your own research before making investment decisions.

**Elliott Wave Theory Notes:**
- Impulse waves (1-2-3-4-5) move in the direction of the main trend
- Corrective waves (A-B-C) move against the main trend
- Wave validation checks classic Elliott Wave rules but patterns may vary

**Data Source:** Yahoo Finance
""")
