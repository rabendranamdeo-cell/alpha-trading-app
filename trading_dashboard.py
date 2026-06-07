import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Page config
st.set_page_config(page_title="Alpha Trading Analytics Dashboard", page_icon="📈", layout="wide")

# Custom CSS for Premium Look
st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border-left: 5px solid #3b82f6; }
    h1, h2, h3 { color: #f3f4f6; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    div.stButton > button:first-child { background-color: #2563eb; color: white; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("📈 Alpha Trading Analytics Dashboard v1.0")
st.subheader("Intraday 15-Minute Technical Scanner & Pattern Detector")

# Sidebar - Settings & Watchlist
st.sidebar.header("🛠️ Dashboard Settings")
watchlist = st.sidebar.multiselect(
    "Select Stocks for Watchlist:",
    ["ADANIPORTS", "CGPOWER", "DIXON", "SUNPHARMA", "RELIANCE", "TATASTEEL", "INFY"],
    default=["ADANIPORTS", "CGPOWER", "DIXON", "SUNPHARMA"]
)

timeframe = st.sidebar.selectbox("Select Timeframe:", ["15 Minute", "5 Minute", "1 Hour", "Daily"], index=0)
risk_reward_ratio = st.sidebar.slider("Risk to Reward Ratio (1:X):", 1.5, 4.0, 2.0, 0.5)

# Mock Data Generator for Demonstration (Since yfinance needs live internet/installation)
def generate_mock_data(stock, periods=100):
    np.random.seed(42 if stock == "ADANIPORTS" else 7)
    base_price = {"ADANIPORTS": 1350, "CGPOWER": 650, "DIXON": 9800, "SUNPHARMA": 1500}.get(stock, 1000)
    
    dates = pd.date_range(end=datetime.now(), periods=periods, freq='15min')
    close = base_price + np.random.randn(periods).cumsum() * (base_price * 0.005)
    open_p = close + np.random.randn(periods) * (base_price * 0.002)
    high = np.maximum(open_p, close) + np.random.rand(periods) * (base_price * 0.003)
    low = np.minimum(open_p, close) - np.random.rand(periods) * (base_price * 0.003)
    volume = np.random.randint(10000, 50000, size=periods)
    
    df = pd.DataFrame({'Open': open_p, 'High': high, 'Low': low, 'Close': close, 'Volume': volume}, index=dates)
    
    # Calculate Technical Indicators
    # 1. MACD
    df['EMA12'] = df['Close'].ewm(span=12, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = df['EMA12'] - df['EMA26']
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # 2. VWAP
    df['VWAP'] = (df['Volume'] * (df['High'] + df['Low'] + df['Close']) / 3).cumsum() / df['Volume'].cumsum()
    
    # 3. Supertrend (Simplified)
    df['ATR'] = (df['High'] - df['Low']).rolling(window=14).mean().fillna(base_price*0.01)
    df['Supertrend'] = df['Close'].rolling(window=7).mean() - (1.5 * df['ATR'])
    df['ST_Trend'] = np.where(df['Close'] > df['Supertrend'], "Bullish", "Bearish")
    
    return df

# Main Dashboard Grid
if not watchlist:
    st.warning("Please select at least one stock from the sidebar.")
else:
    # 1. Overview Cards
    st.markdown("### 📊 Market Live Overview")
    cols = st.columns(len(watchlist))
    
    selected_stock_data = {}
    
    for i, stock in enumerate(watchlist):
        df = generate_mock_data(stock)
        selected_stock_data[stock] = df
        last_row = df.iloc[-1]
        prev_row = df.iloc[-2]
        price_change = last_row['Close'] - prev_row['Close']
        pct_change = (price_change / prev_row['Close']) * 100
        
        with cols[i]:
            st.metric(
                label=f"{stock} (15m)",
                value=f"₹{last_row['Close']:.2f}",
                delta=f"{price_change:+.2f} ({pct_change:+.2f}%)"
            )

    # 2. Technical Scanner Table
    st.markdown("### 🔍 Technical Indicator Scanner")
    scanner_data = []
    for stock in watchlist:
        df = selected_stock_data[stock]
        last = df.iloc[-1]
        
        # Determine signals
        macd_signal = "BUY (Bullish Crossover)" if last['MACD'] > last['Signal_Line'] else "SELL (Bearish Crossover)"
        vwap_signal = "Above VWAP (Bullish)" if last['Close'] > last['VWAP'] else "Below VWAP (Bearish)"
        st_signal = last['ST_Trend']
        
        # Check Patterns
        pattern = "Neutral"
        # Bearish Engulfing check
        p_open, p_close = df.iloc[-2]['Open'], df.iloc[-2]['Close']
        c_open, c_close = df.iloc[-1]['Open'], df.iloc[-1]['Close']
        if p_close > p_open and c_open > c_close and c_open >= p_close and c_close <= p_open:
            pattern = "🔴 Bearish Engulfing"
        elif last['High'] >= df['High'].max() * 0.995 and df.iloc[-15]['High'] >= df['High'].max() * 0.995:
            pattern = "⚠️ Potential Double Top"
            
        scanner_data.append({
            "Stock Name": stock,
            "Current Price": f"₹{last['Close']:.2f}",
            "MACD Status": macd_signal,
            "VWAP Status": vwap_signal,
            "Supertrend": st_signal,
            "Pattern Detected": pattern
        })
        
    st.table(pd.DataFrame(scanner_data))

    # 3. Interactive Charts & Calculator
    st.markdown("### 📈 Visual Chart Analysis & Trade Calculator")
    selected_chart_stock = st.selectbox("Choose stock to view detailed chart & trade plan:", watchlist)
    
    df_chart = selected_stock_data[selected_chart_stock]
    last_idx = df_chart.index[-1]
    last_row = df_chart.iloc[-1]
    
    # Plotly Chart
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df_chart.index[-40:],
        open=df_chart['Open'].tail(40),
        high=df_chart['High'].tail(40),
        low=df_chart['Low'].tail(40),
        close=df_chart['Close'].tail(40),
        name='Candlestick'
    ))
    fig.add_trace(go.Scatter(x=df_chart.index[-40:], y=df_chart['VWAP'].tail(40), line=dict(color='orange', width=1.5), name='VWAP'))
    fig.add_trace(go.Scatter(x=df_chart.index[-40:], y=df_chart['Supertrend'].tail(40), line=dict(color='green', width=1.5), name='Supertrend'))
    
    fig.update_layout(title=f"{selected_chart_stock} Technical Chart", template="plotly_dark", xaxis_rangeslider_visible=False, height=450)
    st.plotly_chart(fig, use_container_width=True)
    
    # 4. Smart Target & Stop Loss Calculator
    st.markdown("### 🧮 Automatic Trade Risk Calculator")
    calc_col1, calc_col2 = st.columns(2)
    
    with calc_col1:
        trade_type = st.radio("Select Trade Direction:", ["BUY (Long)", "SELL (Short)"])
        entry_price = st.number_input("Confirm Entry Price (₹):", value=float(round(last_row['Close'], 2)))
        
    with calc_col2:
        # Calculate SL based on ATR or recent low
        atr_value = last_row['ATR']
        if trade_type == "BUY (Long)":
            stop_loss = entry_price - (1.5 * atr_value)
            target = entry_price + ((entry_price - stop_loss) * risk_reward_ratio)
        else:
            stop_loss = entry_price + (1.5 * atr_value)
            target = entry_price - ((stop_loss - entry_price) * risk_reward_ratio)
            
        st.markdown(f"""
        <div style='background-color:#1e293b; padding:20px; border-radius:8px; border-left: 5px solid #10b981;'>
            <h4>🎯 Automated Trade Setup Plan:</h4>
            <p><b>Suggested Entry:</b> ₹{entry_price:.2f}</p>
            <p style='color:#ef4444;'><b>Strict Stop-Loss (SL):</b> ₹{stop_loss:.2f}</p>
            <p style='color:#10b981;'><b>Target Profit (T1):</b> ₹{target:.2f}</p>
            <p><i>Risk-Reward Ratio set to 1:{risk_reward_ratio}</i></p>
        </div>
        """, unsafe_allow_html=True)

st.sidebar.info("Pro Tip: For publishing to Play Store, this exact logic can be converted into a Flutter app with a cloud database subscription model.")