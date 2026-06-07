import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NIFTY Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>⚡ NIFTY Momentum Scanner</h1>", unsafe_allow_html=True)

# Sidebar UI
st.sidebar.header("Scanner Settings")
side = st.sidebar.selectbox("Market Direction", ["Bullish", "Bearish"])

# Using checkboxes instead of multiselect to keep it lightweight
use_ema = st.sidebar.checkbox("EMA 20", value=True)
use_rsi = st.sidebar.checkbox("RSI", value=False)
use_vol = st.sidebar.checkbox("Volume Spike", value=False)

def get_indicators(df):
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['VolAvg'] = df['Volume'].rolling(20).mean()
    return df

tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "LT.NS", "ITC.NS", "SBIN.NS"]

if st.sidebar.button("Scan"):
    data = yf.download(tickers, period="6mo", group_by='ticker', progress=False)
    results = []
    for symbol in tickers:
        df = get_indicators(data[symbol].copy())
        p = df['Close'].iloc[-1]
        
        # Logic
        hit = False
        if side == "Bullish":
            if (use_ema and p > df['EMA20'].iloc[-1]) or \
               (use_rsi and df['RSI'].iloc[-1] > 60) or \
               (use_vol and df['Volume'].iloc[-1] > df['VolAvg'].iloc[-1] * 1.5):
                hit = True
        else:
            if (use_ema and p < df['EMA20'].iloc[-1]) or \
               (use_rsi and df['RSI'].iloc[-1] < 40) or \
               (use_vol and df['Volume'].iloc[-1] > df['VolAvg'].iloc[-1] * 1.5):
                hit = True
        
        if hit: results.append({"Ticker": symbol, "Price": f"₹{p:.2f}"})
            
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.write("No matches found.")
