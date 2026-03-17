import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "Heavy Engine Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper().strip()
        ticker_sym = f"{s}.NS"
        
        # Simple download without custom sessions to avoid curl_cffi error
        df = yf.download(ticker_sym, period="2y", interval="1d", progress=False)

        if df.empty or len(df) < 200:
            return {"symbol": s, "error": "Insufficient history or Yahoo busy", "score": 0}

        # Handle potential multi-index
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # 📊 HEAVY INDICATORS
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)

        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        sma200 = float(df['SMA200'].iloc[-1])
        ema20 = float(df['EMA20'].iloc[-1])

        # Scoring Logic
        score = 0
        if cp > sma200: score += 4  # Accuracy: Trend is your friend
        if cp > ema20: score += 3
        if 40 < rsi < 65: score += 3

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "score": score,
            "trend": "BULLISH" if cp > sma200 else "BEARISH",
            "signal": "STRONG BUY 🚀" if score >= 8 else "BUY ✅" if score >= 6 else "WAIT ⏳"
        }
    except Exception as e:
        return {"error": "Technical Sync Issue", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))