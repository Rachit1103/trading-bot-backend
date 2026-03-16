import pandas as pd
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "Professional Stooq Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper().strip()
        # Stooq format for Indian Stocks: SYMBOL.IN
        stooq_sym = f"{s}.IN"
        
        # Stooq se CSV data download karein (Free & No Block)
        url = f"https://stooq.com/q/d/l/?s={stooq_sym}&i=d"
        df = pd.read_csv(url)

        if df.empty or len(df) < 50:
            return {"symbol": s, "error": "Data not available for this symbol", "score": 0}

        # Rename columns for calculation
        df.columns = ['Date', 'Open', 'High', 'Low', 'Close', 'Volume']
        df['Close'] = df['Close'].astype(float)

        # --- HEAVY ACCURACY INDICATORS ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['SMA200'] = ta.sma(df['Close'], length=200)

        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 50
        ema20 = float(df['EMA20'].iloc[-1]) if not pd.isna(df['EMA20'].iloc[-1]) else cp
        sma200 = float(df['SMA200'].iloc[-1]) if not pd.isna(df['SMA200'].iloc[-1]) else cp

        # Scoring Logic (High Accuracy)
        score = 0
        if 40 < rsi < 65: score += 3  # Momentum check
        if cp > ema20: score += 3     # Trend check
        if cp > sma200: score += 4    # Golden Rule: Buy only above 200 SMA

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": score,
            "signal": "STRONG BUY 🚀" if score >= 7 else "BUY ✅" if score >= 5 else "WAIT ⏳"
        }
    except Exception as e:
        return {"error": "Service Busy", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))