import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ta
import requests
---------------------------------------

1. Title & Page Configuration

---------------------------------------

st.set_page_config(page_title="AI Forex Signal Dashboard", layout="wide") st.title("📊 AI-Powered Forex Signal Dashboard")

---------------------------------------

2. Forex Symbol Selector

---------------------------------------

symbols = { "EUR/USD": ("EUR", "USD"), "GBP/USD": ("GBP", "USD"), "USD/JPY": ("USD", "JPY"), "USD/CHF": ("USD", "CHF"), "AUD/USD": ("AUD", "USD"), "USD/CAD": ("USD", "CAD") }

pair = st.selectbox("Choose Forex Pair", list(symbols.keys())) from_symbol, to_symbol = symbols[pair]

strict_mode = st.toggle("🔒 Strict Signal Mode", value=True)

---------------------------------------

3. Get Forex Data from TwelveData

---------------------------------------

def get_data(symbol1, symbol2): api_key = "your_twelvedata_api_key_here"  # Replace with your actual TwelveData API key url = f"https://api.twelvedata.com/time_series?symbol={symbol1}/{symbol2}&interval=15min&outputsize=50&apikey={api_key}" r = requests.get(url) data = r.json()

if 'values' not in data:
    st.error("Error fetching data. Please check your API key and symbol.")
    return pd.DataFrame()

df = pd.DataFrame(data['values'])
df = df.rename(columns={
    "datetime": "date",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close"
})
df = df.astype({"open": float, "high": float, "low": float, "close": float})
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date')
return df

---------------------------------------

4. Generate Indicators & Signal

---------------------------------------

def generate_signal(df, strict=False): df['ema10'] = ta.trend.ema_indicator(df['close'], window=10) df['ema20'] = ta.trend.ema_indicator(df['close'], window=20) df['ema50'] = ta.trend.ema_indicator(df['close'], window=50) df['rsi'] = ta.momentum.rsi(df['close'], window=14) df['macd'] = ta.trend.macd_diff(df['close']) bb = ta.volatility.BollingerBands(df['close'], window=20, window_dev=2) df['bb_upper'] = bb.bollinger_hband() df['bb_lower'] = bb.bollinger_lband() df['atr'] = ta.volatility.average_true_range(df['high'], df['low'], df['close'], window=14)

last = df.iloc[-1]
prev = df.iloc[-2]

signal = "WAIT"
entry = sl = tp = None
confidence = 0

if strict:
    if (
        last['close'] > last['ema10'] > last['ema20'] > last['ema50'] and
        last['rsi'] > 55 and last['rsi'] < 70 and
        last['macd'] > 0 and last['macd'] > prev['macd'] and
        (last['close'] - last['open']) > 0 and
        (last['close'] - last['low']) > 0.7 * (last['high'] - last['low'])
    ):
        signal = "BUY"
        entry = round(last['close'], 5)
        sl = round(entry - last['atr'], 5)
        tp = round(entry + (last['atr'] * 1.8), 5)
        confidence = 95

    elif (
        last['close'] < last['ema10'] < last['ema20'] < last['ema50'] and
        last['rsi'] < 45 and last['rsi'] > 30 and
        last['macd'] < 0 and last['macd'] < prev['macd'] and
        (last['open'] - last['close']) > 0 and
        (last['high'] - last['close']) > 0.7 * (last['high'] - last['low'])
    ):
        signal = "SELL"
        entry = round(last['close'], 5)
        sl = round(entry + last['atr'], 5)
        tp = round(entry - (last['atr'] * 1.8), 5)
        confidence = 95

else:
    if last['close'] < last['ema10'] < last['ema20'] and last['rsi'] < 45 and last['macd'] < 0:
        signal = "SELL"
        entry = round(last['close'], 5)
        sl = round(entry + 0.0015, 5)
        tp = round(entry - 0.0025, 5)
        confidence = 75
    elif last['close'] > last['ema10'] > last['ema20'] and last['rsi'] > 55 and last['macd'] > 0:
        signal = "BUY"
        entry = round(last['close'], 5)
        sl = round(entry - 0.0015, 5)
        tp = round(entry + 0.0025, 5)
        confidence = 75

binary = "UP" if signal == "BUY" else "DOWN" if signal == "SELL" else "NO ACTION"
return signal, entry, sl, tp, binary, confidence

---------------------------------------

5. Plot Chart

---------------------------------------

def plot_chart(df): fig = go.Figure() fig.add_trace(go.Candlestick( x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name='Price')) fig.add_trace(go.Scatter(x=df['date'], y=df['ema10'], line=dict(color='orange'), name='EMA 10')) fig.add_trace(go.Scatter(x=df['date'], y=df['ema20'], line=dict(color='red'), name='EMA 20')) fig.add_trace(go.Scatter(x=df['date'], y=df['ema50'], line=dict(color='gray'), name='EMA 50')) fig.add_trace(go.Scatter(x=df['date'], y=df['bb_upper'], line=dict(color='blue', dash='dot'), name='BB Upper')) fig.add_trace(go.Scatter(x=df['date'], y=df['bb_lower'], line=dict(color='blue', dash='dot'), name='BB Lower')) fig.update_layout(height=500, margin=dict(l=0, r=0, t=0, b=0)) st.plotly_chart(fig, use_container_width=True)

---------------------------------------

6. Main App Logic

---------------------------------------

with st.spinner("Fetching chart and generating signal..."): df = get_data(from_symbol, to_symbol)

if not df.empty:
    signal, entry, sl, tp, binary, confidence = generate_signal(df, strict=strict_mode)
    plot_chart(df)

    st.subheader("💡 Trade Signal")
    if signal == "WAIT":
        st.info("No safe signal detected right now. Wait for trend confirmation.")
    else:
        st.success(f"{signal} Signal ✅")
        st.metric("Entry Price", entry)
        st.metric("Stop Loss", sl)
        st.metric("Take Profit", tp)
        st.metric("Confidence Score", f"{confidence}%")

    st.subheader("📍 Binary Option Direction")
    if binary != "NO ACTION":
        st.success(f"Next 15-min Candle Expected: {binary}")
    else:
        st.warning("Binary direction unclear — wait for setup.")

