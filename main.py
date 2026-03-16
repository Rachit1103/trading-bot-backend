import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "AI Trader Pro Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        # Bharat ke stocks ke liye .NS lagana zaroori hai
        ticker_sym = f"{s}.NS" if not (s.endswith(".NS") or s.endswith(".BO")) else s
        
        # 1 saal ka data download karein taaki 200 SMA sahi nikal sake
        df = yf.download(ticker_sym, period="1y", interval="1d", progress=False)

        if df.empty or len(df) < 200:
            return {"symbol": symbol, "error": f"Insufficient Data (Need 200+ days, got {len(df)})", "score": 0}

        # Indicators Calculation
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        
        # Current Values extract karein
        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        macd_line = float(macd.iloc[-1, 0]) 
        signal_line = float(macd.iloc[-1, 2])
        ema20 = float(df['EMA_20'].iloc[-1])
        sma200 = float(df['SMA_200'].iloc[-1])
        vol_curr = float(df['Volume'].iloc[-1])
        vol_ma = float(ta.sma(df['Volume'], length=20).iloc[-1])

        # Scoring Logic (Simple 10 point scale)
        score = 0
        if rsi < 40: score += 2
        if rsi > 60: score -= 1
        if macd_line > signal_line: score += 2
        if cp > ema20: score += 2
        if cp > sma200: score += 2
        if vol_curr > vol_ma: score += 2

        # Final Score adjustment
        final_score = max(0, min(10, score))
        
        signal = "WAIT"
        if final_score >= 7: signal = "BUY"
        elif final_score <= 3: signal = "SELL"

        return {
            "symbol": ticker_sym,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": final_score,
            "signal": signal
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)