import streamlit as st
import yfinance as yf
import pandas as pd

# Page setup
st.set_page_config(page_title="NIFTY 100 Scanner", layout="wide")
st.markdown("<h1 style='text-align: center;'>⚡ NIFTY 100 Momentum Scanner</h1>", unsafe_allow_html=True)

# Sidebar
st.sidebar.header("Scanner Settings")
side = st.sidebar.selectbox("Market Direction", ["Bullish", "Bearish"])

# Checkboxes
use_ema9 = st.sidebar.checkbox("EMA 9", value=True)
use_ema26 = st.sidebar.checkbox("EMA 26", value=True)
use_rsi = st.sidebar.checkbox("RSI", value=True)

# Indicator functions
def get_indicators(df):
    df['Close'] = pd.to_numeric(df['Close'], errors='coerce')
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# NIFTY 100 List
tickers = [
    "ABB.NS", "ADANIENT.NS", "ADANIGREEN.NS", "ADANIPORTS.NS", "ADANIPOWER.NS", 
    "AMBUJACEM.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS", 
    "BAJAJFINSV.NS", "BAJFINANCE.NS", "BANKBARODA.NS", "BERGEPAINT.NS", "BHARTIARTL.NS", 
    "BPCL.NS", "BRITANNIA.NS", "CANBK.NS", "CHOLAFIN.NS", "CIPLA.NS", 
    "COALINDIA.NS", "DABUR.NS", "DIVISLAB.NS", "DLF.NS", "DRREDDY.NS", 
    "EICHERMOT.NS", "GAIL.NS", "GODREJCP.NS", "GRASIM.NS", "HCLTECH.NS", 
    "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", 
    "ICICIBANK.NS", "ICICIPRULI.NS", "INDIGO.NS", "INDUSINDBK.NS", "INDUSTOWER.NS", 
    "INFY.NS", "IOC.NS", "ITC.NS", "JIOFIN.NS", "JSWENERGY.NS", 
    "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", 
    "MARUTI.NS", "MAXHEALTH.NS", "NESTLEIND.NS", "NTPC.NS", "ONGC.NS", 
    "PIDILITIND.NS", "PNB.NS", "POWERGRID.NS", "PFC.NS", "RECLTD.NS", 
    "RELIANCE.NS", "SBICARD.NS", "SBILIFE.NS", "SBIN.NS", "SHREECEM.NS", 
    "SIEMENS.NS", "SUNPHARMA.NS", "TATACOMM.NS", "TATACONSUM.NS", "TATAMOTORS.NS", 
    "TATAPOWER.NS", "TATASTEEL.NS", "TCS.NS", "TECHM.NS", "TITAN.NS", 
    "TORNTPHARM.NS", "TRENT.NS", "TVSMOTOR.NS", "UPL.NS", "ULTRACEMCO.NS", 
    "UNIONBANK.NS", "UNITDSPR.NS", "VBL.NS", "VEDL.NS", "WIPRO.NS", 
    "ZOMATO.NS", "ZYDUSLIFE.NS"
]

if st.sidebar.button("Scan"):
    results = []
    progress_bar = st.progress(0)
    
    for i, symbol in enumerate(tickers):
        try:
            df = yf.download(symbol, period="6mo", progress=False)
            if not df.empty:
                df = get_indicators(df.copy())
                p = df['Close'].iloc[-1]
                ema9 = df['EMA9'].iloc[-1]
                ema26 = df['EMA26'].iloc[-1]
                rsi = df['RSI'].iloc[-1]
                
                hit = False
                if side == "Bullish":
                    if (use_ema9 and ema9 < p) or (use_ema26 and ema26 < ema9) or (use_rsi and rsi > 60):
                        hit = True
                else:
                    if (use_ema9 and ema9 > p) or (use_ema26 and ema26 > ema9) or (use_rsi and rsi < 30):
                        hit = True
                
                if hit:
                    results.append({"Ticker": symbol, "Price": f"₹{p:.2f}", "RSI": f"{rsi:.1f}"})
        except Exception:
            continue
        progress_bar.progress((i + 1) / len(tickers))
            
    if results:
        st.table(pd.DataFrame(results))
    else:
        st.write("No matches found. Try adjusting indicator settings.")
