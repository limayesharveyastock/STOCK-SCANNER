import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io

st.set_page_config(layout="wide", page_title="NIFTY 200 Momentum Scanner")
st.title("⚡ NIFTY 200 Momentum Scanner")

# --- 1. Fetch NIFTY 200 Tickers ---
@st.cache_data(ttl=86400)
def get_nifty_200_tickers():
    # URL for NIFTY 200 list
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        return (df['Symbol'].astype(str) + ".NS").tolist()
    except:
        st.error("Failed to fetch NIFTY 200 list.")
        return []

# --- 2. Indicator Calculation ---
def calculate_metrics(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # RSI Calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 3. Scanning Engine ---
if 'master_df' not in st.session_state:
    st.session_state.master_df = None

if st.button("Run NIFTY 200 Scan"):
    with st.spinner("Analyzing NIFTY 200..."):
        tickers = get_nifty_200_tickers()
        results = []
        bar = st.progress(0)
        
        for i, t in enumerate(tickers):
            try:
                df = yf.download(t, period="2mo", interval="1d", progress=False)
                if not df.empty and len(df) > 30:
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    df = calculate_metrics(df)
                    last = df.iloc[-1]
                    
                    if pd.notnull(last['RSI']):
                        results.append({
                            "Ticker": t.replace(".NS", ""),
                            "Price": round(float(last['Close']), 2),
                            "EMA9": round(float(last['EMA9']), 2),
                            "EMA26": round(float(last['EMA26']), 2),
                            "RSI": round(float(last['RSI']), 2)
                        })
            except: continue
            bar.progress((i + 1) / len(tickers))
        st.session_state.master_df = pd.DataFrame(results)
    st.rerun()

# --- 4. Filtering Interface ---
if st.session_state.master_df is not None and not st.session_state.master_df.empty:
    df = st.session_state.master_df
    
    st.sidebar.header("Filter Criteria")
    min_rsi, max_rsi = st.sidebar.slider("RSI Range", 0.0, 100.0, (30.0, 70.0))
    bullish_ema = st.sidebar.checkbox("Bullish Crossover (EMA9 > EMA26)", True)
    
    filtered_df = df[(df['RSI'] >= min_rsi) & (df['RSI'] <= max_rsi)]
    if bullish_ema:
        filtered_df = filtered_df[filtered_df['EMA9'] > filtered_df['EMA26']]
            
    st.write(f"### Results ({len(filtered_df)} stocks found)")
    st.table(filtered_df.sort_values(by='RSI', ascending=False))
