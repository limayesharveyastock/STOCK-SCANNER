import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="NIFTY 500 Scanner", layout="wide")
st.title("⚡ NIFTY 500 Daily Momentum Scanner")

# --- Indicators ---
def get_indicators(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # RSI calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- Main Scan ---
if st.sidebar.button("Run Scan"):
    # Using a subset for immediate testing - you can expand this to 500
    tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS"] 
    results = []
    
    progress_bar = st.progress(0)
    for i, t in enumerate(tickers):
        try:
            # Daily data is more reliable for 500 tickers than 15m
            df = yf.download(t, period="3mo", interval="1d", progress=False)
            if len(df) < 30: continue
            
            df = get_indicators(df.copy())
            last = df.iloc[-1]
            
            # BROADENED LOGIC: Changed to OR so you get results
            # Trigger if: Price above EMA9 OR EMA9 crosses EMA26 OR RSI is strong
            if (last['Close'] > last['EMA9']) or (last['EMA9'] > last['EMA26']) or (last['RSI'] > 60):
                results.append({
                    "Ticker": t,
                    "Price": f"{last['Close']:.2f}",
                    "RSI": f"{last['RSI']:.1f}",
                    "Status": "Momentum Detected"
                })
        except:
            continue
        progress_bar.progress((i + 1) / len(tickers))

    if results:
        st.table(pd.DataFrame(results))
    else:
        st.write("No matches found. Try adjusting the thresholds.")
