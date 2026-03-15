from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import uvicorn
import os

app = FastAPI()

# CORS allow karna zaroori hai taaki mobile app connect ho sake
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "AI Trading Backend is Running"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        # Indian stocks ke liye .NS automatic add karna
        s = symbol.upper()
        if not s.endswith(".NS"):
            ticker_sym = f"{s}.NS"
        else:
            ticker_sym = s

        df = yf.download(ticker_sym, period="60d", interval="1d", progress=False)
        
        if df.empty:
            return {"symbol": symbol, "error": "No data found", "score": 0}

        # Technical Indicators calculation
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        
        current_price = round(float(df['Close'].iloc[-1]), 2)
        rsi_val = float(df['RSI'].iloc[-1])
        ema_val = float(df['EMA_20'].iloc[-1])
        
        # Simple AI Scoring Logic
        score = 0
        if rsi_val < 40: score += 4  # Oversold (Buying zone)
        if rsi_val > 70: score -= 2  # Overbought
        if current_price > ema_val: score += 4 # Bullish trend
        
        signal = "NEUTRAL"
        if score >= 7: signal = "STRONG BUY"
        elif score >= 5: signal = "BUY"
        elif score <= 3: signal = "SELL"

        return {
            "symbol": ticker_sym,
            "current_price": current_price,
            "rsi": round(rsi_val, 2),
            "signal": signal,
            "score": max(0, score)
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    # Render automatically port assign karta hai
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)