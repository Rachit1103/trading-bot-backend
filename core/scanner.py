import yfinance as yf
import pandas as pd
import requests

# Session to avoid IP Blocking
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
})

def calculate_master_score(symbol):
    try:
        s = symbol.strip().upper()
        if not s.endswith(".NS") and not s.startswith("^"):
            s = f"{s}.NS"

        # Fetch data with session headers
        ticker = yf.Ticker(s, session=session)
        df = ticker.history(period="5d", interval="1d")

        if df.empty:
            return {"symbol": s.replace(".NS",""), "current_price": 0, "score": 0, "signal": "OFFLINE"}

        price = round(float(df['Close'].iloc[-1]), 2)
        
        # Scoring Logic: Price Movement + Trend
        score = 5
        if len(df) >= 2:
            change = df['Close'].iloc[-1] - df['Close'].iloc[-2]
            if change > 0: score = 9 # Strong Bullish
            else: score = 3          # Bearish

        return {
            "symbol": s.replace(".NS", ""),
            "current_price": price,
            "score": int(score),
            "signal": "BUY" if score >= 8 else "WAIT"
        }
    except Exception as e:
        print(f"Error for {symbol}: {e}")
        return {"symbol": symbol, "current_price": 0, "score": 0, "signal": "ERROR"}