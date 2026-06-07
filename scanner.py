import requests
import io
import time
import numpy as np
import pandas as pd
import yfinance as yf
from tqdm import tqdm

# --- helper indicators ---
def ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def wma(series, length):
    weights = np.arange(1, length+1)
    return series.rolling(length).apply(lambda x: np.dot(x, weights)/weights.sum(), raw=True)

def rsi(series, length=14):
    delta = series.diff()
    up = delta.clip(lower=0)
    down = -1 * delta.clip(upper=0)
    ma_up = up.rolling(length).mean()
    ma_down = down.rolling(length).mean()
    rs = ma_up / (ma_down.replace(0, np.nan))
    return 100 - (100 / (1 + rs))

def supertrend(df, length=12, multiplier=2.5):
    hl2 = (df['High'] + df['Low']) / 2
    atr = df['High'].combine(df['Low'], max) - df['Low'].combine(df['High'], min)
    atr = df['High'].rolling(length).max() - df['Low'].rolling(length).min()
    # Use True ATR (simplified): use pandas' rolling average of TR
    tr1 = df['High'] - df['Low']
    tr2 = (df['High'] - df['Close'].shift()).abs()
    tr3 = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    final_upper = upperband.copy()
    final_lower = lowerband.copy()
    trend = pd.Series(True, index=df.index)  # True = uptrend
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
    st = final_lower.where(trend, final_upper)
    return st

# --- load NIFTY 500 tickers from official CSV ---
CSV_URL = "https://nsearchives.nseindia.com/content/indices/ind_nifty500list.csv"
r = requests.get(CSV_URL)
tickers = []
if r.ok:
    df_list = pd.read_csv(io.StringIO(r.text))
    tickers = (df_list['Symbol'].astype(str) + ".NS").tolist()
else:
    raise SystemExit("Failed to download NIFTY 500 list. See NSE site.")

# --- scanning function ---
def scan_tickers(tickers, batch_size=50):
    matches = []
    for i in range(0, len(tickers), batch_size):
        batch = tickers[i:i+batch_size]
        data = yf.download(batch, period="7d", interval="15m", group_by='ticker', threads=True, progress=False)
        for t in batch:
            try:
                df = data[t].dropna().copy()
                if df.shape[0] < 60: continue
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
                    matches.append({
                        'Ticker': t.replace('.NS',''),
                        'Close': last['Close'],
                        'EMA9': last['EMA9'],
                        'EMA26': last['EMA26'],
                        'RSI20_WMA': last['RSI20_WMA'],
                        'SuperTrend': last['ST'],
                        'Volume': int(last['Volume']),
                        'Vol_MA50': int(last['Vol_MA50'])
                    })
            except Exception:
                continue
        time.sleep(1)  # polite pause
    return pd.DataFrame(matches)

if __name__ == "__main__":
    result = scan_tickers(tickers)
    print(result.to_string(index=False))
    result.to_csv("nifty500_scan_results.csv", index=False)
