import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import io

st.set_page_config(layout="wide", page_title="NIFTY 200 Filterable Screener")
st.title("⚡ NIFTY 200 Filterable Screener")

# --- Data Collection Logic ---
@st.cache_data(ttl=86400)
def get_nifty_200_tickers():
    url = "https://nsearchives.nseindia.com/content/indices/ind_nifty200list.csv"
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        df = pd.read_csv(io.StringIO(response.text))
        return (df['Symbol'].astype(str) + ".NS").tolist()
    except: return []

def calculate_metrics(df):
    # EMA Calculation
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    # RSI Calculation (14 period)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- UI & State Management ---
if 'master_df' not in st.session_state:
    st.session_state.master_df = None

if st.button("Run Full NIFTY 200 Scan"):
    with st.spinner("Processing NIFTY 200..."):
        tickers = get_nifty_200_tickers()
        results = []
        bar = st.progress(0)
        for i, t in enumerate(tickers):
            try:
                df = yf.download(t, period="1mo", interval="1d", progress=False)
                if not df.empty and len(df) > 30:
                    if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                    df = calculate_metrics(df)
                    last = df.iloc[-1]
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

# --- Filtering Section ---
if st.session_state.master_df is not None:
    st.sidebar.header("Filter Criteria")
    df = st.session_state.master_df
    
    # Range Slider for RSI
    min_rsi, max_rsi = st.sidebar.slider("RSI Range", 0.0, 100.0, (30.0, 70.0))
    # Toggle for EMA Crossover
    bullish_only = st.sidebar.checkbox("EMA 9 > EMA 26 (Bullish Trend)", True)
    
    # Applying Filters
    filtered_df = df[(df['RSI'] >= min_rsi) & (df['RSI'] <= max_rsi)]
    if bullish_only:
        filtered_df = filtered_df[filtered_df['EMA9'] > filtered_df['EMA26']]
        
    st.write(f"### Results ({len(filtered_df)} stocks)")
    st.table(filtered_df.sort_values(by='RSI', ascending=False))
