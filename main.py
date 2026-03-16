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
    return {"status": "Safe Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker_sym = f"{s}.NS" if not (s.endswith(".NS") or s.endswith(".BO")) else s
        
        # Download data with a small delay to avoid blocking
        df = yf.download(ticker_sym, period="1y", interval="1d", progress=False)

        if df.empty or len(df) < 50:
            return {"symbol": symbol, "error": "Rate Limited or No Data", "score": 0}

        # Indicators Calculation
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA'] = ta.ema(df['Close'], length=20)

        # GET LATEST VALUES (Safest Method)
        cp = float(df['Close'].values[-1])
        
        # RSI Check
        rsi_val = df['RSI'].values[-1]
        rsi = float(rsi_val) if rsi_val is not None else 50
        
        # EMA Check
        ema_val = df['EMA'].values[-1]
        ema = float(ema_series.values[-1]) if ema_val is not None else cp

        score = 0
        if rsi < 40: score += 5
        if cp > ema: score += 5

        return {
            "symbol": ticker_sym,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": score,
            "signal": "BUY" if score >= 5 else "WAIT"
        }
    except Exception as e:
        return {"error": "Server Busy, Try Again", "details": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))