import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import requests
import io
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="NIFTY500 15m Scanner")

# -------------------------
# Indicator helpers
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
    hl2 = (df['High'] + df['Low']) / 2
    # True Range
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift()).abs()
    tr3 = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)

    final_upper = upperband.copy()
    final_lower = lowerband.copy()
    trend = pd.Series(True, index=df.index)

    for i in range(1, len(df)):
        if df['Close'].iat[i-1] <= final_upper.iat[i-1]:
            final_upper.iat[i] = min(upperband.iat[i], final_upper.iat[i-1])
        if df['Close'].iat[i-1] >= final_lower.iat[i-1]:
            final_lower.iat[i] = max(lowerband.iat[i], final_lower.iat[i-1])

        if df['Close'].iat[i] > final_upper.iat[i-1]:
            trend.iat[i] = True
        elif df['Close'].iat[i] < final_lower.iat[i-1]:
            trend.iat[i] = False
        else:
            trend.iat[i] = trend.iat[i-1]
            if trend.iat[i] and final_lower.iat[i] < final_lower.iat[i-1]:
                final_lower.iat[i] = final_lower.iat[i-1]
            if (not trend.iat[i]) and final_upper.iat[i] > final_upper.iat[i-1]:
                final_upper.iat[i] = final_upper.iat[i-1]

    st_val = final_lower.where(trend, final_upper)
    return st_val

# -------------------------
# Load NIFTY 500 tickers
# -------------------------
@st.cache_data(ttl=3600)
def load_nifty500_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    tickers = (df['Symbol'].astype(str) + ".NS").tolist()
    return tickers

# -------------------------
# Fetch and compute for one ticker
# -------------------------
def process_ticker(ticker, period_days=7):
    try:
        df = yf.download(ticker, period=f"{period_days}d", interval="15m", progress=False, threads=False)
        if df is None or df.empty or len(df) < 60:
            return None
        df = df.dropna().copy()
        df['EMA9'] = ema(df['Close'], 9)
        df['EMA26'] = ema(df['Close'], 26)
        df['RSI20'] = rsi(df['Close'], 20)
        df['RSI20_WMA'] = wma(df['RSI20'], 20)
        df['ST'] = supertrend(df, length=12, multiplier=2.5)
        df['Vol_MA50'] = df['Volume'].rolling(50).mean()
        last = df.iloc[-1]
        cond = (
            (last['EMA9'] > last['Close']) and
            (last['EMA26'] < last['EMA9']) and
            (last['RSI20_WMA'] > 60) and
            (last['ST'] < last['Close']) and
            (last['Volume'] > last['Vol_MA50'])
        )
        if cond:
            return {
                'Ticker': ticker.replace('.NS',''),
                'Close': float(last['Close']),
                'EMA9': float(last['EMA9']),
                'EMA26': float(last['EMA26']),
                'RSI20_WMA': float(last['RSI20_WMA']),
                'SuperTrend': float(last['ST']),
                'Volume': int(last['Volume']),
                'Vol_MA50': int(last['Vol_MA50'])
            }
    except Exception:
        return None
    return None

# -------------------------
# UI
# -------------------------
st.title("NIFTY500 15m Scanner — EMA/RSI/SuperTrend/Volume")

col1, col2 = st.columns([1, 3])

with col1:
    st.markdown("**Scan settings**")
    tickers = load_nifty500_tickers()
    st.write(f"Loaded **{len(tickers)}** tickers from NIFTY500")
    max_workers = st.slider("Parallel workers (threads)", min_value=4, max_value=32, value=12)
    batch_days = st.slider("History (days) for indicators", min_value=3, max_value=14, value=7)
    run_scan = st.button("Run scan now")
    auto_refresh = st.checkbox("Auto refresh every 5 minutes", value=False)

with col2:
    st.markdown("**Matches**")
    placeholder = st.empty()

# -------------------------
# Scanning logic (threaded)
# -------------------------
def run_scan_and_collect():
    results = []
    progress_bar = st.progress(0)
    total = len(tickers)
    completed = 0
    futures = []
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for t in tickers:
            futures.append(ex.submit(process_ticker, t, batch_days))
        for f in as_completed(futures):
            completed += 1
            progress_bar.progress(int(completed / total * 100))
            res = f.result()
            if res:
                results.append(res)
    return pd.DataFrame(results)

# -------------------------
# Main execution
# -------------------------
if run_scan:
    with st.spinner("Scanning NIFTY500 (this may take several minutes)..."):
        df_matches = run_scan_and_collect()
    if df_matches is None or df_matches.empty:
        placeholder.info("No matches found for the current rules.")
    else:
        placeholder.dataframe(df_matches.sort_values("Ticker").reset_index(drop=True))
        st.download_button("Download results CSV", df_matches.to_csv(index=False), file_name="nifty500_scan_results.csv")

    # show chart for first match
    if df_matches is not None and not df_matches.empty:
        sel = st.selectbox("Inspect ticker", df_matches['Ticker'].tolist())
        if sel:
            ticker_full = sel + ".NS"
            df_chart = yf.download(ticker_full, period=f"{batch_days}d", interval="15m", progress=False)
            df_chart = df_chart.dropna()
            df_chart['EMA9'] = ema(df_chart['Close'], 9)
            df_chart['EMA26'] = ema(df_chart['Close'], 26)
            df_chart['RSI20'] = rsi(df_chart['Close'], 20)
            df_chart['RSI20_WMA'] = wma(df_chart['RSI20'], 20)
            df_chart['ST'] = supertrend(df_chart, length=12, multiplier=2.5)

            fig = go.Figure()
            fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'],
                                         low=df_chart['Low'], close=df_chart['Close'], name='Price'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA9'], line=dict(color='orange'), name='EMA9'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['EMA26'], line=dict(color='purple'), name='EMA26'))
            fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['ST'], line=dict(color='green'), name='SuperTrend'))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("**RSI (20) and WMA(20) of RSI**")
            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI20'], name='RSI20'))
            fig2.add_trace(go.Scatter(x=df_chart.index, y=df_chart['RSI20_WMA'], name='RSI20_WMA'))
            fig2.add_hline(y=60, line_dash="dash", line_color="red")
            st.plotly_chart(fig2, use_container_width=True)

# -------------------------
# Auto refresh
# -------------------------
if auto_refresh:
    st.experimental_rerun()

st.markdown("---")
st.markdown("**Notes**: 1) Yahoo Finance may throttle requests; for faster/real-time scanning use a paid data API. 2) Validate signals with backtesting before trading.")
