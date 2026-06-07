import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

st.set_page_config(page_title="Professional NIFTY Scanner", layout="wide")

# Center the header
st.markdown("<h1 style='text-align: center; color: #1f77b4;'>⚡ NIFTY Pro-Momentum Scanner</h1>", unsafe_allow_html=True)

# Sidebar UI
st.sidebar.header("📊 Scanner Parameters")
side = st.sidebar.selectbox("Market Direction", ["Bullish", "Bearish"])
indicators = st.sidebar.multiselect("Select Active Signals (OR logic)", ["EMA 20", "RSI", "Supertrend", "Volume Spike"])

# NIFTY 50 Full List
tickers = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS", "LT.NS", "ITC.NS", "SBIN.NS", "BHARTIARTL.NS", "KOTAKBANK.NS"]

if st.sidebar.button("Run Professional Scan"):
    with st.spinner("Processing market data..."):
        data = yf.download(tickers, period="6mo", group_by='ticker', progress=False)
        results = []
        
        for symbol in tickers:
            try:
                df = data[symbol].copy()
                # Advanced Indicators
                df['EMA20'] = ta.ema(df['Close'], length=20)
                df['RSI'] = ta.rsi(df['Close'], length=14)
                st_data = ta.supertrend(df['High'], df['Low'], df['Close'], length=7, multiplier=3)
                df = pd.concat([df, st_data], axis=1)
                df['VolAvg'] = df['Volume'].rolling(20).mean()
                
                p = df['Close'].iloc[-1]
                
                # Logic
                hit = False
                if side == "Bullish":
                    if ("EMA 20" in indicators and p > df['EMA20'].iloc[-1]) or \
                       ("RSI" in indicators and df['RSI'].iloc[-1] > 60) or \
                       ("Supertrend" in indicators and df.iloc[-1, -3] == 1) or \
                       ("Volume Spike" in indicators and df['Volume'].iloc[-1] > df['VolAvg'].iloc[-1] * 1.5):
                        hit = True
                else:
                    if ("EMA 20" in indicators and p < df['EMA20'].iloc[-1]) or \
                       ("RSI" in indicators and df['RSI'].iloc[-1] < 40) or \
                       ("Supertrend" in indicators and df.iloc[-1, -3] == -1) or \
                       ("Volume Spike" in indicators and df['Volume'].iloc[-1] > df['VolAvg'].iloc[-1] * 1.5):
                        hit = True
                
                if hit: results.append({"Ticker": symbol, "Price": p})
            except: continue
            
        if results:
            df_res = pd.DataFrame(results)
            st.table(df_res)
            # Add Professional CSV Download
            csv = df_res.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Export Results to CSV", data=csv, file_name="scan_results.csv", mime="text/csv")
        else:
            st.warning("No matches found. Please adjust your indicator selection.")
