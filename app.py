import streamlit as st
import pandas as pd
from kiteconnect import KiteConnect
import io
import requests

# --- 1. Setup Kite ---
# Use st.secrets to keep your keys safe!
kite = KiteConnect(api_key=st.secrets["api_key"])
kite.set_access_token(st.secrets["access_token"])

@st.cache_data(ttl=86400)
def get_instrument_map():
    """Downloads the master list and creates a {symbol: token} map."""
    url = "https://api.kite.trade/instruments"
    headers = {"Authorization": f"token {st.secrets['api_key']}:{st.secrets['access_token']}"}
    response = requests.get(url, headers=headers)
    df = pd.read_csv(io.StringIO(response.text))
    # Filter for NSE and map symbol to token
    nse_df = df[df['exchange'] == 'NSE']
    return dict(zip(nse_df['tradingsymbol'], nse_df['instrument_token']))

def calculate_metrics(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# --- 2. Scanning Engine ---
if st.button("Run NIFTY 200 Scan via Kite"):
    instr_map = get_instrument_map()
    # Replace this with your actual NIFTY 200 symbol list
    nifty200_symbols = ["RELIANCE", "TCS", "INFY"] # Add all 200 here
    
    results = []
    for symbol in nifty200_symbols:
        token = instr_map.get(symbol)
        if token:
            # Fetch last 30 days of daily data
            data = kite.historical_data(token, from_date="2026-05-07", to_date="2026-06-07", interval="day")
            df = pd.DataFrame(data)
            df = calculate_metrics(df)
            last = df.iloc[-1]
            results.append({
                "Ticker": symbol,
                "Price": round(float(last['Close']), 2),
                "EMA9": round(float(last['EMA9']), 2),
                "EMA26": round(float(last['EMA26']), 2),
                "RSI": round(float(last['RSI']), 2)
            })
    st.session_state.master_df = pd.DataFrame(results)
    st.rerun()
