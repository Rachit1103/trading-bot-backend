import pandas as pd
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import io

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "AI Trader Pro - Stooq Engine Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper().strip()
        # Stooq format: TCS.IN
        url = f"https://stooq.com/q/d/l/?s={s}.IN&i=d"
        
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return {"error": "Stooq Server Down"}

        df = pd.read_csv(io.StringIO(response.text))

        if df.empty or len(df) < 10:
            return {"symbol": s, "error": "No Data Found on Stooq", "score": 0}

        # Clean Column Names (Stooq sometimes sends 'Close' or '收盘')
        df.columns = [c.capitalize() for c in df.columns]
        
        # Ensure 'Close' exists
        if 'Close' not in df.columns:
            return {"error": "Invalid Data Format"}

        # --- HEAVY ACCURACY LOGIC ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        macd = ta.macd(df['Close'])

        # Latest Values
        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1]) if not pd.isna(df['RSI'].iloc[-1]) else 50
        ema20 = float(df['EMA20'].iloc[-1]) if not pd.isna(df['EMA20'].iloc[-1]) else cp
        sma200 = float(df['SMA200'].iloc[-1]) if not pd.isna(df['SMA200'].iloc[-1]) else cp

        # Scoring (Out of 10)
        score = 0
        if 40 < rsi < 65: score += 3
        if cp > ema20: score += 3
        if cp > sma200: score += 4 # Accuracy: SMA 200 is King

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": score,
            "signal": "STRONG BUY 🚀" if score >= 8 else "BUY ✅" if score >= 6 else "WAIT ⏳"
        }
    except Exception as e:
        return {"error": "Logic Error", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))