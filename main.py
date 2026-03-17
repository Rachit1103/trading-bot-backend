import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🗂️ Scanned Stocks ki History (Database)
scanned_history = []

@app.get("/")
def home():
    return {"status": "Global Scanner Active", "total_scanned": len(scanned_history)}

# 📜 Saare scanned stocks dekhne ke liye
@app.get("/all_stocks")
def get_all_stocks():
    return {"history": scanned_history}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper().strip()
        ticker_sym = f"{s}.NS"
        
        # Smart Fetch logic
        stock = yf.Ticker(ticker_sym)
        df = stock.history(period="2y", interval="1d", auto_adjust=True)

        if df.empty or len(df) < 200:
            return {"error": f"Data not found for {s}"}

        # --- 🚀 20 INDICATOR ENGINE ---
        score = 0
        cp = float(df['Close'].iloc[-1])
        
        # Indicators Calculation
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        
        # Scoring
        if cp > df['SMA200'].iloc[-1]: score += 4
        if cp > df['EMA20'].iloc[-1]: score += 3
        if 45 < df['RSI'].iloc[-1] < 65: score += 3
        
        final_score = round(score, 1)
        signal = "STRONG BUY 🚀" if final_score >= 8 else "BUY ✅" if final_score >= 6 else "WAIT ⏳"
        if cp < df['SMA200'].iloc[-1]: signal = "BEARISH / AVOID 🛑"

        result = {
            "symbol": s,
            "price": round(cp, 2),
            "score": f"{final_score}/10",
            "signal": signal,
            "trend": "Bullish" if cp > df['SMA200'].iloc[-1] else "Bearish"
        }

        # ✅ Automatically add to History if not exists
        if s not in scanned_history:
            scanned_history.append(s)

        return result

    except Exception as e:
        return {"error": "Processing error", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))