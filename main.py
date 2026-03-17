import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "Single-Scan Engine Active"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        # Step 1: Human-like delay taaki Yahoo block na kare
        time.sleep(2)
        
        s = symbol.upper().strip()
        ticker_sym = f"{s}.NS"
        
        # Step 2: Sirf utna hi data mangao jitna zaroori hai
        # Hum 1.5 saal ka data lenge SMA 200 ke liye (kam load)
        ticker = yf.Ticker(ticker_sym)
        df = ticker.history(period="500d", interval="1d", auto_adjust=True)

        if df.empty or len(df) < 200:
            return {"symbol": s, "error": "No Data or Market Closed", "score": 0}

        # Step 3: Heavy Accuracy Indicators
        # SMA 200 (Long term trend line)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        # EMA 20 (Short term momentum)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        # RSI 14 (Strength)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        sma200 = float(df['SMA200'].iloc[-1])
        ema20 = float(df['EMA20'].iloc[-1])

        # Step 4: Accurate Scoring (Out of 10)
        score = 0
        # Condition 1: Price above SMA 200 (The Golden Rule)
        if cp > sma200: score += 4 
        # Condition 2: Price above EMA 20 (Strong Move)
        if cp > ema20: score += 3
        # Condition 3: RSI is healthy (Not overbought)
        if 40 < rsi < 65: score += 3

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": score,
            "trend": "Strong Bullish" if cp > sma200 else "Weak/Bearish",
            "signal": "STRONG BUY 🚀" if score >= 8 else "BUY ✅" if score >= 6 else "WAIT ⏳"
        }
    except Exception as e:
        return {"error": "Server is resting, try in 1 minute", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))