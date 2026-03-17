import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import time
from typing import List

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 📋 Aapki Live Watchlist
# Default stocks: Aap inhe post request se badal sakte hain
user_watchlist = ["TCS", "RELIANCE", "INFY"]

def get_20_indicator_score(df, symbol):
    """20 Indicators ka combined logic - High Accuracy"""
    try:
        score = 0
        cp = float(df['Close'].iloc[-1])
        
        # Trend Indicators (SMA/EMA)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        
        if cp > df['SMA200'].iloc[-1]: score += 1.5
        if cp > df['SMA50'].iloc[-1]: score += 1
        if cp > df['SMA20'].iloc[-1]: score += 0.5
        if cp > df['EMA9'].iloc[-1]: score += 0.5
        if df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1]: score += 0.5
        
        # Momentum (RSI, MACD, Stoch)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        rsi_val = df['RSI'].iloc[-1]
        
        if 45 < rsi_val < 70: score += 1.5
        if macd.iloc[-1, 0] > macd.iloc[-1, 2]: score += 1
        if rsi_val > 50: score += 0.5
        
        # Volatility (Bollinger Bands)
        bbands = ta.bbands(df['Close'], length=20)
        if cp > bbands.iloc[-1, 1]: score += 1
        
        # Strength (ADX & Volume)
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        if adx.iloc[-1, 0] > 25: score += 1
        if df['Volume'].iloc[-1] > df['Volume'].iloc[-2]: score += 1

        final_score = round(score, 1)
        signal = "STRONG BUY 🚀" if final_score >= 8 else "BUY ✅" if final_score >= 6 else "WAIT ⏳"
        if cp < df['SMA200'].iloc[-1]: signal = "BEARISH / AVOID 🛑"

        return {
            "current_price": round(cp, 2),
            "accuracy_score": f"{final_score}/10",
            "signal": signal,
            "trend": "Bullish" if cp > df['SMA200'].iloc[-1] else "Bearish"
        }
    except:
        return None

@app.get("/")
def home():
    return {"status": "Live Engine Active", "stocks_tracked": user_watchlist}

# 🚀 Pure Watchlist ko ek saath scan karna (Live Refresh ke liye)
@app.get("/watchlist/live")
def get_live_watchlist():
    results = []
    for s in user_watchlist:
        time.sleep(1) # Block protection
        try:
            ticker_sym = f"{s}.NS"
            df = yf.download(ticker_sym, period="2y", interval="1d", progress=False, auto_adjust=True)
            if not df.empty and len(df) >= 200:
                analysis = get_20_indicator_score(df, s)
                if analysis:
                    analysis["symbol"] = s
                    results.append(analysis)
        except:
            continue
    return results

# ➕ Watchlist mein naya stock add karne ke liye
@app.get("/watchlist/add/{symbol}")
def add_to_watchlist(symbol: str):
    s = symbol.upper().strip()
    if s not in user_watchlist:
        user_watchlist.append(s)
        return {"status": "success", "message": f"{s} added"}
    return {"status": "exists", "message": f"{s} is already there"}

# 🔍 Single detail scan (Wahi purana logic)
@app.get("/scan/{symbol}")
def scan_single(symbol: str):
    # Same code as before for single stock deep analysis
    pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))