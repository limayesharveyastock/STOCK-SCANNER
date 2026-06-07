import streamlit as st
import yfinance as yf
import pandas as pd

st.title("🔍 Smoke Test: Data Verification")

if st.button("Verify Data Connectivity"):
    # Testing just 5 tickers to see if they pull data at all
    test_tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS"]
    data_log = []
    
    for t in test_tickers:
        # Fetching Daily data (more reliable than 15m)
        df = yf.download(t, period="1mo", interval="1d", progress=False)
        if not df.empty:
            last = df.iloc[-1]
            data_log.append({
                "Ticker": t,
                "Close": float(last['Close']),
                "Volume": int(last['Volume'])
            })
    
    if data_log:
        st.table(pd.DataFrame(data_log))
        st.success("Data successfully retrieved from Yahoo Finance.")
    else:
        st.error("Scanner failed to retrieve data. Check your connection or API status.")
