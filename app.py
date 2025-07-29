import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import ta
import requests

# -------------------------------
# Page Config & Header
# -------------------------------
st.set_page_config(page_title="Strict AI Forex Planner", layout="wide")
st.title("🔒 AI Forex Smart Entry Planner (Strict Mode)")

# -------------------------------
# Symbol Selector
# -------------------------------
symbols = {
    "EUR/USD": ("EUR", "USD"),
    "GBP/USD": ("GBP", "USD"),
    "USD/JPY": ("USD", "JPY"),
    "USD/CHF": ("USD", "CHF"),
    "AUD/USD": ("AUD", "USD"),
    "USD/CAD": ("USD", "CAD")
}
pair = st.selectbox("Select Forex Pair", list(symbols.keys()))
from_symbol, to_symbol = symbols[pair]

# -------------------------------
# Data Loader
# -------------------------------
def get_data(sym1, sym2):
    api_key = "806dd29a09244737ae6cd1a305061557"  # Replace with your real TwelveData API key
    url = f"https://api.twelvedata.com/time_series?symbol={sym1}/{sym2}&interval=15min&outputsize=50&apikey={api_key}"
    r = requests.get(url)
    data = r.json()

    if "values" not in data:
        st.error("Failed to fetch data. Check API key or currency pair.")
        return pd.DataFrame()

    df = pd.DataFrame(data["values"])
    df = df.rename(columns={"datetime": "date", "open": "open", "high": "high", "low": "low", "close": "close"})

    # ✅ Only convert OHLC to float
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)
    df["close"] = df["close"].astype(float)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    return df

# -------------------------------
# Indicator & AI Analysis Logic
# -------------------------------
def analyze(df):
    df["ema10"] = ta.trend.ema_indicator(df["close"], window=10)
    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)
    df["macd"] = ta.trend.macd_diff(df["close"])
    df["atr"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    signal = "WAIT"
    confidence = 0
    entry = sl = tp = None
    reason = ""

    # ✅ Strict BUY logic
    if (
        last["close"] > last["ema10"] > last["ema20"] > last["ema50"] and
        last["macd"] > 0 and last["macd"] > prev["macd"] and
        last["rsi"] > 55 and last["rsi"] < 70
    ):
        entry = round(last["ema20"], 5)
        sl = round(entry - last["atr"], 5)
        tp = round(entry + last["atr"] * 2, 5)
        confidence = 99
        signal = "BUY"
        reason = "EMA Uptrend + MACD Momentum + RSI Strength"

    # ✅ Strict SELL logic
    elif (
        last["close"] < last["ema10"] < last["ema20"] < last["ema50"] and
        last["macd"] < 0 and last["macd"] < prev["macd"] and
        last["rsi"] < 45
    ):
        entry = round(last["ema20"], 5)
        sl = round(entry + last["atr"], 5)
        tp = round(entry - last["atr"] * 2, 5)
        confidence = 99
        signal = "SELL"
        reason = "EMA Downtrend + MACD Weakness + RSI Drop"

    return signal, entry, sl, tp, confidence, reason

# -------------------------------
# Chart Plotter
# -------------------------------
def plot(df):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df["date"], open=df["open"], high=df["high"],
        low=df["low"], close=df["close"], name="Candles"
    ))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ema10"], name="EMA10", line=dict(color="orange")))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ema20"], name="EMA20", line=dict(color="red")))
    fig.add_trace(go.Scatter(x=df["date"], y=df["ema50"], name="EMA50", line=dict(color="gray")))
    fig.update_layout(height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# -------------------------------
# App Main Logic
# -------------------------------
with st.spinner("Analyzing market..."):
    df = get_data(from_symbol, to_symbol)

    if not df.empty:
        signal, entry, sl, tp, confidence, reason = analyze(df)
        plot(df)

        st.subheader("💡 AI Smart Trade Plan")
        if signal == "WAIT":
            st.info("🕒 No confirmed setup now. Wait for the perfect zone.")
        else:
            st.success(f"{signal} SIGNAL ✅ (Confidence: {confidence}%)")
            st.metric("🔹 Suggested Entry", entry)
            st.metric("🛡️ Stop Loss", sl)
            st.metric("🎯 Take Profit", tp)
            st.caption(f"🧠 Reason: {reason}")
