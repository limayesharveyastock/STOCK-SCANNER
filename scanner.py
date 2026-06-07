import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="NIFTY500 High-Speed Scanner")

# -------------------------
# High-Performance Indicators
# -------------------------
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def wma(series, length):
    weights = np.arange(1, length + 1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(length).mean()
    ma_down = down.rolling(length).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def supertrend(df, length=12, multiplier=2.5):
    # Calculate ATR (Vectorized)
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    
    # Calculate Bands
    hl2 = (df['High'] + df['Low']) / 2
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    
    # Vectorized trend detection
    trend = np.zeros(len(df))
    st = np.zeros(len(df))
    
    # Optimized loop for trend logic
    for i in range(1, len(df)):
        if df['Close'].iloc[i] > upperband.iloc[i-1]:
            trend[i] = 1
        elif df['Close'].iloc[i] < lowerband.iloc[i-1]:
            trend[i] = -1
        else:
            trend[i] = trend[i-1]
            if trend[i] == 1 and lowerband.iloc[i] < lowerband.iloc[i-1]:
                lowerband.iloc[i] = lowerband.iloc[i-1]
            elif trend[i] == -1 and upperband.iloc[i] > upperband.iloc[i-1]:
                upperband.iloc[i] = upperband.iloc[i-1]
        st[i] = lowerband.iloc[i] if trend[i] == 1 else upperband.iloc[i]
        
    return pd.Series(st, index=df.index)

# -------------------------
# Data Loading
# -------------------------
@st.cache_data(ttl=3600)
def load_nifty500_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    r = requests.get(url, timeout=10)
    df = pd.read_csv(io.StringIO(r.text))
    return (df['Symbol'].astype(str) + ".NS").tolist()

# -------------------------
# Ticker Processor
# -------------------------
def process_ticker(ticker, period_days=7):
    try:
        df = yf.download(ticker, period=f"{period_days}d", interval="15m", progress=False, threads=False)
        if df is None or df.empty or len(df) < 60: return None
        
        df['EMA9'] = ema(df['Close'], 9)
        df['EMA26'] = ema(df['Close'], 26)
        df['RSI20'] = rsi(df['Close'], 20)
        df['RSI20_WMA'] = wma(df['RSI20'], 20)
        df['ST'] = supertrend(df, length=12, multiplier=2.5)
        df['Vol_MA50'] = df['Volume'].rolling(50).mean()
        
        last = df.iloc[-1]
        # Confluence logic
        if (last['EMA9'] > last['Close']) and (last['EMA26'] < last['EMA9']) and \
           (last['RSI20_WMA'] > 60) and (last['ST'] < last['Close']) and (last['Volume'] > last['Vol_MA50']):
            return {
                'Ticker': ticker.replace('.NS',''),
                'Close': float(last['Close']),
                'EMA9': float(last['EMA9']),
                'RSI20_WMA': float(last['RSI20_WMA'])
            }
    except: return None
    return None

# -------------------------
# UI & Execution
# -------------------------
st.title("⚡ NIFTY500 Performance Scanner")
tickers = load_nifty500_tickers()

if st.button("Run High-Speed Scan"):
    results = []
    bar = st.progress(0)
    # Reduced workers to 6 to prevent Yahoo Finance throttling
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(process_ticker, t) for t in tickers]
        for i, f in enumerate(as_completed(futures)):
            res = f.result()
            if res: results.append(res)
            bar.progress((i + 1) / len(tickers))
    
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.write("No matches found. The logic is currently very strict; consider broadening conditions.")
