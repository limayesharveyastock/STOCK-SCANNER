import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="NIFTY500 Scanner")

# --- Optimized Indicator Suite ---
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(length).mean()
    ma_down = down.rolling(length).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def supertrend(df, length=12, multiplier=2.5):
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    
    upperband = ((df['High'] + df['Low']) / 2) + (multiplier * atr)
    lowerband = ((df['High'] + df['Low']) / 2) - (multiplier * atr)
    
    trend = np.zeros(len(df))
    st = np.zeros(len(df))
    
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > upperband.iloc[i-1]: trend[i] = 1
        elif df['Close'].iloc[i] < lowerband.iloc[i-1]: trend[i] = -1
        else:
            trend[i] = trend[i-1]
            if trend[i] == 1 and lowerband.iloc[i] < lowerband.iloc[i-1]: lowerband.iloc[i] = lowerband.iloc[i-1]
            elif trend[i] == -1 and upperband.iloc[i] > upperband.iloc[i-1]: upperband.iloc[i] = upperband.iloc[i-1]
        st[i] = lowerband.iloc[i] if trend[i] == 1 else upperband.iloc[i]
    return pd.Series(st, index=df.index)

# --- Logic Implementation ---
@st.cache_data
def get_tickers():
    try:
        # Reads the local file we created
        df = pd.read_csv("tickers.csv")
        return df['Symbol'].tolist()
    except:
        return ["RELIANCE.NS", "TCS.NS"]

def process_ticker(t):
    try:
        df = yf.download(t, period="10d", interval="15m", progress=False)
        if len(df) < 60: return None
        
        # Calculate indicators...
        df['EMA9'] = ema(df['Close'], 9)
        df['EMA26'] = ema(df['Close'], 26)
        df['RSI'] = rsi(df['Close'], 14)
        df['ST'] = supertrend(df)
        last = df.iloc[-1]
        
        # Return status object instead of None
        return {
            'Ticker': t.replace('.NS', ''),
            'EMA_Cross': last['EMA9'] > last['EMA26'],
            'Above_ST': last['Close'] > last['ST'],
            'RSI_Value': round(last['RSI'], 2)
        }
    except: return None

# --- App UI ---
st.title("⚡ NIFTY 500 Momentum Scanner")
if st.button("Run Scan"):
    tickers = get_tickers()
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(process_ticker, t) for t in tickers]
        for f in as_completed(futures):
            if f.result(): results.append(f.result())
    
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.info("Scan complete: No stocks met the current criteria.")
