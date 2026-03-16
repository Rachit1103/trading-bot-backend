import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "AI Trader Pro Live - AntiBlock Active"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper().strip()
        ticker_sym = f"{s}.NS"
        
        # Use yfinance but with a custom logic
        ticker = yf.Ticker(ticker_sym)
        # 1 saal ka data accuracy ke liye
        df = ticker.history(period="1y")

        if df.empty:
            return {"symbol": s, "error": "No Data - Market Closed or Blocked", "score": 0}

        # --- HEAVY ACCURACY INDICATORS ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        macd = ta.macd(df['Close'])

        # Latest Values
        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1]) if not df['RSI'].empty else 50
        ema20 = float(df['EMA20'].iloc[-1]) if not df['EMA20'].empty else cp
        sma200 = float(df['SMA200'].iloc[-1]) if not df['SMA200'].empty else cp

        # Scoring (Out of 10)
        score = 0
        if rsi < 40: score += 2
        if rsi > 60: score -= 1
        if cp > ema20: score += 3
        if cp > sma200: score += 3
        if not macd.empty and macd.iloc[-1, 0] > macd.iloc[-1, 2]: score += 2

        final_score = max(0, min(10, score))

        return {
            "symbol": ticker_sym,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": final_score,
            "signal": "STRONG BUY 🚀" if final_score >= 8 else "BUY ✅" if final_score >= 6 else "WAIT ⏳"
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))