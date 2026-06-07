import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io

st.set_page_config(layout="wide", page_title="NIFTY 500 Pro Scanner")
st.title("⚡ NIFTY 500 Pro Momentum Scanner")

# --- 1. Dynamic Ticker Loader ---
@st.cache_data(ttl=86400)
def get_nifty_500_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    try:
        # Use headers to mimic a browser to avoid NSE blocks
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        return (df['Symbol'].astype(str) + ".NS").tolist()
    except:
        st.error("Failed to load ticker list. Check internet connection.")
        return []

# --- 2. Indicators ---
def calculate_metrics(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    return df

# --- 3. UI and Scanning ---
if st.button("Run Full NIFTY 500 Scan"):
    tickers = get_nifty_500_tickers()
    if tickers:
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i, t in enumerate(tickers):
            status_text.text(f"Scanning {t} ({i+1}/{len(tickers)})...")
            try:
                # Optimized: Only pull 5 days of 15m data for speed
                df = yf.download(t, period="5d", interval="15m", progress=False)
                
                if not df.empty and len(df) > 20:
                    # Robust column extraction
                    if isinstance(df.columns, pd.MultiIndex):
                        df.columns = df.columns.get_level_values(0)
                    
                    df = calculate_metrics(df)
                    last = df.iloc[-1]
                    
                    # Logic: Bullish EMA Crossover
                    if last['EMA9'] > last['EMA26']:
                        results.append({
                            "Ticker": t.replace(".NS", ""), 
                            "Price": round(float(last['Close']), 2),
                            "EMA9": round(float(last['EMA9']), 2)
                        })
            except:
                continue
            
            progress_bar.progress((i + 1) / len(tickers))
        
        status_text.text("Scan Complete!")
        if results:
            st.table(pd.DataFrame(results))
        else:
            st.warning("Scan finished: No matches found.")
