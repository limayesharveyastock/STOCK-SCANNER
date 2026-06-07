import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="NIFTY Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>⚡ NIFTY Momentum Scanner</h1>", unsafe_allow_html=True)

# Math for indicators (No pandas-ta required)
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
        # Example logic: Ticker shows up if price is above EMA20
        if p > df['EMA20'].iloc[-1]:
            results.append({"Ticker": symbol, "Price": f"₹{p:.2f}"})
            
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.write("No results found.")
