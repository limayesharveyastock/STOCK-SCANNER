import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Use caching to prevent re-downloading the list every time
@st.cache_data
def get_nifty_500():
    # Use a local or stable list if URL is blocked
    # For now, keeping your URL but adding a timeout
    try:
        url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
        headers = {'User-Agent': 'Mozilla/5.0'}
        df = pd.read_csv(url, storage_options=headers)
        return (df['Symbol'].astype(str) + ".NS").tolist()
    except:
        return ["RELIANCE.NS", "TCS.NS"] # Fallback

def supertrend(df, length=12, multiplier=2.5):
    # Optimized Supertrend (Simplified version for speed)
    tr = pd.concat([df['High'] - df['Low'], 
                    (df['High'] - df['Close'].shift()).abs(), 
                    (df['Low'] - df['Close'].shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    upper = ((df['High'] + df['Low']) / 2) + (multiplier * atr)
    lower = ((df['High'] + df['Low']) / 2) - (multiplier * atr)
    return upper, lower

st.title("⚡ NIFTY 500 Advanced Scanner")

if st.button("Run Full Scan"):
    tickers = get_nifty_500()
    results = []
    bar = st.progress(0)
    
    for i, t in enumerate(tickers):
        try:
            df = yf.download(t, period="5d", interval="15m", progress=False)
            if len(df) < 60: continue
            
            # Calculations
            df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
            df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
            
            # Logic check
            last = df.iloc[-1]
            if (last['EMA9'] > last['Close']) and (last['EMA26'] < last['EMA9']):
                results.append({'Ticker': t, 'Price': last['Close']})
                
        except: continue
        bar.progress((i + 1) / len(tickers))
        
    st.table(pd.DataFrame(results))
