import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "Backend Live - Robust Version"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker_sym = f"{s}.NS" if not (s.endswith(".NS") or s.endswith(".BO")) else s
        
        # 1. Download Data
        df = yf.download(ticker_sym, period="1y", interval="1d", progress=False)
        if df.empty or len(df) < 50:
            return {"symbol": symbol, "error": "Insufficient Data", "score": 0}

        # 2. Indicators Calculation with Safety
        rsi_series = ta.rsi(df['Close'], length=14)
        ema_series = ta.ema(df['Close'], length=20)
        macd_df = ta.macd(df['Close'])

        # 3. Safe Extraction Function
        def get_val(series):
            if series is not None and not series.empty:
                return float(series.iloc[-1])
            return None

        cp = float(df['Close'].iloc[-1])
        rsi = get_val(rsi_series)
        ema20 = get_val(ema_series)
        
        # MACD validation
        macd_val = None
        signal_val = None
        if macd_df is not None and not macd_df.empty:
            macd_val = float(macd_df.iloc[-1, 0])
            signal_val = float(macd_df.iloc[-1, 2])

        # 4. Scoring with "None" checks
        score = 0
        if rsi and rsi < 40: score += 2
        if ema20 and cp > ema20: score += 2
        if macd_val and signal_val and macd_val > signal_val: score += 2
        if rsi and rsi > 65: score -= 1

        final_score = max(0, min(10, score))

        return {
            "symbol": ticker_sym,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2) if rsi else 0,
            "score": int(final_score),
            "signal": "BUY" if final_score >= 6 else "WAIT"
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)