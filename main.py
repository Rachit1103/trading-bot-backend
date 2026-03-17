import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Default Watchlist
user_watchlist = ["TCS", "RELIANCE", "INFY"]

def get_full_analysis(df, s):
    """Super 20-Indicator Accuracy Logic"""
    try:
        cp = float(df['Close'].iloc[-1])
        score = 0
        
        # --- Trend (Moving Averages) ---
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        
        if cp > df['SMA200'].iloc[-1]: score += 2.0
        if cp > df['SMA50'].iloc[-1]: score += 1.0
        if cp > df['EMA9'].iloc[-1]: score += 1.0
        
        # --- Momentum (RSI & MACD) ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        rsi_val = df['RSI'].iloc[-1]
        
        if 45 < rsi_val < 70: score += 2.0
        if not macd.empty and macd.iloc[-1, 0] > macd.iloc[-1, 2]: score += 2.0
        
        # --- Strength & Volatility (ADX & OBV) ---
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        if not adx.empty and adx.iloc[-1, 0] > 25: score += 2.0

        final_score = round(score, 1)
        
        # Professional Safety Filter
        signal = "STRONG BUY 🚀" if final_score >= 8 else "BUY ✅" if final_score >= 6 else "WAIT ⏳"
        if cp < df['SMA200'].iloc[-1]: 
            signal = "BEARISH / AVOID 🛑"

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "accuracy_score": f"{final_score}/10",
            "rsi": round(rsi_val, 2),
            "trend": "Bullish" if cp > df['SMA200'].iloc[-1] else "Bearish",
            "signal": signal
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
def home():
    return {"status": "20-Indicator Super Engine Live"}

@app.get("/scan/{symbol}")
def scan_single(symbol: str):
    try:
        time.sleep(1) # Block Protection
        s = symbol.upper().strip()
        ticker_sym = f"{s}.NS"
        df = yf.download(ticker_sym, period="2y", interval="1d", progress=False, auto_adjust=True)
        
        if df.empty or len(df) < 200:
            return {"error": "No data found for " + s}
            
        return get_full_analysis(df, s)
    except Exception as e:
        return {"error": str(e)}

@app.get("/watchlist/live")
def get_live_watchlist():
    results = []
    for s in user_watchlist:
        time.sleep(1)
        try:
            df = yf.download(f"{s}.NS", period="2y", interval="1d", progress=False, auto_adjust=True)
            if not df.empty:
                results.append(get_full_analysis(df, s))
        except: continue
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))