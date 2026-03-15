import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "AI Trading Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker_sym = f"{s}.NS" if not s.endswith(".NS") else s
        
        # Safe way to fetch data to avoid Rate Limit
        ticker_obj = yf.Ticker(ticker_sym)
        df = ticker_obj.history(period="1mo", interval="1d", timeout=10)

        if df.empty or len(df) < 10:
            return {"symbol": symbol, "error": "No Data/Rate Limited", "score": 0}

        # Indicators
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        
        current_price = round(float(df['Close'].iloc[-1]), 2)
        rsi_val = float(df['RSI'].iloc[-1]) if not df['RSI'].isnull().all() else 50
        ema_val = float(df['EMA_20'].iloc[-1])
        
        score = 0
        if rsi_val < 40: score += 4
        if rsi_val > 70: score -= 2
        if current_price > ema_val: score += 4
        
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
        return {"error": "Server Busy, Retry in 1min", "score": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)