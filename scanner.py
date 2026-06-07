# Update the indicator calculation function
def get_indicators(df):
    df['EMA9'] = df['Close'].ewm(span=9, adjust=False).mean()
    df['EMA26'] = df['Close'].ewm(span=26, adjust=False).mean()
    
    # RSI calculation
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# ... (Inside your Scan button logic)
        df = get_indicators(data[symbol].copy())
        
        # New Conditions
        if side == "Bullish":
            # EMA(9) < Close AND EMA(26) < EMA(9) AND RSI > 60
            if (df['EMA9'].iloc[-1] < p) and \
               (df['EMA26'].iloc[-1] < df['EMA9'].iloc[-1]) and \
               (df['RSI'].iloc[-1] > 60):
                hit = True
                
        else: # Bearish
            # EMA(9) > Close AND EMA(26) > EMA(9) AND RSI < 30
            if (df['EMA9'].iloc[-1] > p) and \
               (df['EMA26'].iloc[-1] > df['EMA9'].iloc[-1]) and \
               (df['RSI'].iloc[-1] < 30):
                hit = True
