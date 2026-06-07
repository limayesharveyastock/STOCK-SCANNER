import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NIFTY Debugger", layout="wide")
st.title("🔍 Scanner Debugger: Checking Thresholds")

def get_indicators(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

if st.sidebar.button("Run Debug Scan"):
    tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "SBIN.NS"] 
    debug_data = []
    
    for t in tickers:
        df = yf.download(t, period="3mo", interval="1d", progress=False)
        if not df.empty:
            df = get_indicators(df.copy())
            last = df.iloc[-1]
            debug_data.append({
                "Ticker": t,
                "Price": last['Close'],
                "EMA9": last['EMA9'],
                "EMA26": last['EMA26'],
                "RSI": last['RSI']
            })
            
    st.table(pd.DataFrame(debug_data))
    st.write("Compare these values to your settings. If the RSI is 45 and your threshold is 60, you will never get a match.")
