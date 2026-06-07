import streamlit as st
import pandas as pd
import requests
import io
from kiteconnect import KiteConnect
from datetime import datetime, timedelta

# Initialize Kite
kite = KiteConnect(api_key=st.secrets["api_key"])
kite.set_access_token(st.secrets["access_token"])

@st.cache_data(ttl=86400)
def get_instrument_map():
    """Maps symbols to Kite instrument tokens."""
    url = "https://api.kite.trade/instruments"
    headers = {"Authorization": f"token {st.secrets['api_key']}:{st.secrets['access_token']}"}
    response = requests.get(url, headers=headers)
    df = pd.read_csv(io.StringIO(response.text))
    return dict(zip(df['tradingsymbol'], df['instrument_token']))

def calculate_metrics(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + (gain / loss)))
    return df

# Main Logic
if st.button("Scan NIFTY 200"):
    instr_map = get_instrument_map()
    # List your NIFTY 200 symbols here
    symbols = ["RELIANCE", "TCS", "INFY"] # Add full list
    results = []
    
    for sym in symbols:
        token = instr_map.get(sym)
        if token:
            # Fetch last 30 days
            from_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            to_date = datetime.now().strftime('%Y-%m-%d')
            data = kite.historical_data(token, from_date=from_date, to_date=to_date, interval="day")
            df = calculate_metrics(pd.DataFrame(data))
            last = df.iloc[-1]
            results.append({"Ticker": sym, "RSI": round(last['RSI'], 2), "EMA9": round(last['EMA9'], 2)})
            
    st.table(pd.DataFrame(results))
