import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import requests

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🛡️ Anti-Block Session Builder
def get_safe_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Connection': 'keep-alive'
    })
    return session

@app.get("/")
def home():
    return {"status": "Heavy Engine Live & Protected"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper().strip()
        ticker_sym = f"{s}.NS"
        
        # Data download using safe session
        df = yf.download(ticker_sym, period="2y", interval="1d", progress=False, session=get_safe_session())

        if df.empty or len(df) < 200:
            return {"symbol": s, "error": "Insufficient history or busy server", "score": 0}

        # Fix column names for multi-index
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        # --- HEAVY ACCURACY LOGIC ---
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])

        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        sma200 = float(df['SMA200'].iloc[-1])
        ema20 = float(df['EMA20'].iloc[-1])

        # Scoring (Confluence Strategy)
        score = 0
        if cp > sma200: score += 4  # Bullish Trend
        if cp > ema20: score += 3   # Short term momentum
        if 40 < rsi < 65: score += 3 # Strength check

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "score": score,
            "rsi": round(rsi, 2),
            "trend": "BULLISH" if cp > sma200 else "BEARISH",
            "signal": "STRONG BUY 🚀" if score >= 8 else "BUY ✅" if score >= 5 else "WAIT ⏳"
        }
    except Exception as e:
        return {"error": "Server Cool-down", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))