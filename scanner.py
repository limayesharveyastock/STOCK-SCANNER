import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NIFTY Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>⚡ NIFTY Momentum Scanner</h1>", unsafe_allow_html=True)

# Sidebar UI
st.sidebar.header("Scanner Settings")
side = st.sidebar.selectbox("Market Direction", ["Bullish", "Bearish"])

# Using checkboxes for indicators
use_ema9 = st.sidebar.checkbox("EMA 9", value=True)
use_ema26 = st.sidebar.checkbox("EMA 26", value=True)
use_rsi = st.sidebar.checkbox("RSI", value=True)

def get_indicators(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "LT.NS", "ITC.NS", "SBIN.NS"]

if st.sidebar.button("Scan"):
    data = yf.download(tickers, period="6mo", group_by='ticker', progress=False)
    results = []
    for symbol in tickers:
        df = get_indicators(data[symbol].copy())
        p = df['Close'].iloc[-1]
        ema9 = df['EMA9'].iloc[-1]
        ema26 = df['EMA26'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        
        # Logic
        hit = False
        if side == "Bullish":
            # EMA(9) BELOW Close, EMA(26) BELOW EMA(9) & RSI ABOVE 60
            if (use_ema9 and ema9 < p) and (use_ema26 and ema26 < ema9) and (use_rsi and rsi > 60):
                hit = True
        else:
            # EMA(9) ABOVE Close, EMA(26) ABOVE EMA(9) & RSI BELOW 30
            if (use_ema9 and ema9 > p) and (use_ema26 and ema26 > ema9) and (use_rsi and rsi < 30):
                hit = True
        
        if hit: results.append({"Ticker": symbol, "Price": f"₹{p:.2f}"})
            
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.write("No matches found.")
