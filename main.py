import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker_sym = f"{s}.NS" if not (s.endswith(".NS") or s.endswith(".BO")) else s
        
        # Download 1 year data
        df = yf.download(ticker_sym, period="1y", interval="1d", progress=False)

        if df.empty or len(df) < 200:
            return {"symbol": symbol, "error": "Insufficient Data", "score": 0}

        # Calculate Indicators using pandas_ta
        rsi_series = ta.rsi(df['Close'], length=14)
        ema_series = ta.ema(df['Close'], length=20)
        sma_series = ta.sma(df['Close'], length=200)
        macd_df = ta.macd(df['Close'])

        # GET LATEST VALUES (Using .values[-1] to avoid Series error)
        cp = float(df['Close'].values[-1])
        rsi = float(rsi_series.values[-1])
        ema20 = float(ema_series.values[-1])
        sma200 = float(sma_series.values[-1])
        macd_val = float(macd_df.iloc[-1, 0])
        signal_val = float(macd_df.iloc[-1, 2])

        # Simple Scoring
        score = 0
        if rsi < 40: score += 2
        if cp > ema20: score += 2
        if cp > sma200: score += 2
        if macd_val > signal_val: score += 2
        if rsi > 60: score -= 1

        final_score = max(0, min(10, score))

        return {
            "symbol": ticker_sym,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": int(final_score),
            "signal": "BUY" if final_score >= 6 else "WAIT"
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)