import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Indicator Helpers ---
def ema(series, span): return series.ewm(span=span, adjust=False).mean()
def rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(length).mean()
    ma_down = down.rolling(length).mean()
    rs = ma_up / ma_down.replace(0, np.nan)
    return 100 - (100 / (1 + rs))

def supertrend(df, length=12, multiplier=2.5):
    hl2 = (df['High'] + df['Low']) / 2
    tr = pd.concat([df['High'] - df['Low'], (df['High'] - df['Close'].shift()).abs(), 
                    (df['Low'] - df['Close'].shift()).abs()], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
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

# --- Processor ---
def process_ticker(t):
    try:
        df = yf.download(t, period="10d", interval="15m", progress=False)
        if df.empty or len(df) < 60: return None
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
        df['EMA9'] = ema(df['Close'], 9)
        df['EMA26'] = ema(df['Close'], 26)
        df['RSI'] = rsi(df['Close'], 14)
        df['ST'] = supertrend(df)
        
        last = df.iloc[-1]
        val = {k: float(v.iloc[0] if hasattr(v, 'iloc') else v) for k, v in last.items()}
        
        # RELAXED LOGIC: Returns data if ANY condition is met for visibility
        if (val['EMA9'] > val['EMA26']) or (val['Close'] > val['ST']) or (val['RSI'] > 55):
            return {
                'Ticker': t.replace('.NS', ''), 
                'Close': val['Close'], 
                'RSI': round(val['RSI'], 2),
                'EMA_Cross': val['EMA9'] > val['EMA26'],
                'Above_ST': val['Close'] > val['ST']
            }
    except: return None
    return None

# --- UI ---
st.title("⚡ NIFTY500 Momentum Explorer")
if st.button("Run Scan"):
    tickers = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "SBIN.NS"] 
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = [ex.submit(process_ticker, t) for t in tickers]
        for f in as_completed(futures):
            if f.result(): results.append(f.result())
    
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.error("No data retrieved. Check ticker list or internet connectivity.")
