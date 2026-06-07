import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NIFTY 100 Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>⚡ NIFTY 100 Debug Scanner</h1>", unsafe_allow_html=True)

side = st.sidebar.selectbox("Market Direction", ["Bullish", "Bearish"])
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"] # Shortened for test

def get_indicators(df):
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

if st.sidebar.button("Scan"):
    results = []
    for symbol in tickers:
        df = yf.download(symbol, period="6mo", progress=False)
        if not df.empty:
            df = get_indicators(df.copy())
            p = df['Close'].iloc[-1]
            ema9 = df['EMA9'].iloc[-1]
            ema26 = df['EMA26'].iloc[-1]
            rsi = df['RSI'].iloc[-1]
            
            # Add to results regardless of logic to test if data comes back
            results.append({
                "Ticker": symbol, 
                "Price": f"₹{p:.2f}", 
                "EMA9": f"{ema9:.2f}", 
                "RSI": f"{rsi:.1f}"
            })
            
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.write("No data returned from Yahoo Finance. Check ticker symbols.")
