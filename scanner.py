import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page configuration
st.set_page_config(page_title="NIFTY 500 Advanced Scanner", layout="wide")
st.title("⚡ NIFTY 500 Full Momentum Scanner")

# Function to generate NIFTY 500 Ticker List
@st.cache_data
def get_nifty_500_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        df = pd.read_csv(url)
        return (df['Symbol'].astype(str) + ".NS").tolist()
    except:
        return []

# --- Indicators ---
def get_indicators(df):
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df['Volume'] = pd.to_numeric(df['Volume'], errors='coerce')
    
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # SuperTrend
    atr = (df['High'] - df['Low']).rolling(14).mean()
    df['ST'] = ((df['High'] + df['Low']) / 2) + (2.5 * atr)
    
    df['Vol_MA50'] = df['Volume'].rolling(50).mean()
    return df

# --- UI and Execution ---
if st.sidebar.button("Run Full NIFTY 500 Scan"):
    tickers = get_nifty_500_tickers()
    if not tickers:
        st.error("Could not fetch NIFTY 500 list.")
    else:
        results = []
        bar = st.progress(0)
        
        for i, t in enumerate(tickers):
            try:
                df = yf.download(t, period="6mo", interval="1d", progress=False)
                if len(df) < 60: continue
                
                df = get_indicators(df.copy())
                last = df.iloc[-1]
                
                # Logic: Trend Momentum OR Strength
                is_bullish = (last['EMA9'] > last['EMA26']) and (last['Close'] > last['ST'])
                is_strong = (last['RSI'] > 55) and (last['Volume'] > last['Vol_MA50'])
                
                if is_bullish or is_strong:
                    results.append({
                        "Ticker": t,
                        "Price": f"{last['Close']:.2f}",
                        "EMA9": f"{last['EMA9']:.2f}",
                        "RSI": f"{last['RSI']:.1f}",
                        "Vol_Spike": last['Volume'] > last['Vol_MA50']
                    })
            except: continue
            bar.progress((i + 1) / len(tickers))

        if results:
            st.table(pd.DataFrame(results))
        else:
            st.write("No matches found.")
