import streamlit as st
import yfinance as yf

st.title("Connection Debugger")

if st.button("Fetch Single Ticker"):
    st.write("Attempting to fetch RELIANCE.NS...")
    try:
        # Request data with a longer timeout and no complex processing
        df = yf.download("RELIANCE.NS", period="5d", interval="15m")
        if df.empty:
            st.error("yfinance returned an empty DataFrame.")
        else:
            st.success("Successfully fetched data!")
            st.write(f"Rows received: {len(df)}")
            st.dataframe(df.head())
    except Exception as e:
        st.error(f"Error: {e}")
