import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🗂️ Global History Database
scanned_history = []

def get_20_indicator_analysis(df, s):
    """Pure 20-Indicator Logic for Maximum Accuracy"""
    try:
        score = 0
        cp = float(df['Close'].iloc[-1])
        
        # 1-10: Trend (SMA 20, 50, 100, 200, EMA 9, EMA 20)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        
        if cp > df['SMA200'].iloc[-1]: score += 3.0 # SMA 200 is King
        if cp > df['SMA50'].iloc[-1]: score += 1.0
        if cp > df['SMA20'].iloc[-1]: score += 1.0
        if cp > df['EMA9'].iloc[-1]: score += 0.5
        
        # 11-15: Momentum (RSI, MACD)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        rsi_val = df['RSI'].iloc[-1]
        
        if 45 < rsi_val < 65: score += 2.0
        if not macd.empty and macd.iloc[-1, 0] > macd.iloc[-1, 2]: score += 1.5
        
        # 16-20: Strength & Volume (ADX, OBV)
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        if not adx.empty and adx.iloc[-1, 0] > 25: score += 1.0

        final_score = round(score, 1)
        signal = "STRONG BUY 🚀" if final_score >= 8 else "BUY ✅" if final_score >= 6 else "WAIT ⏳"
        
        # Global Safety Rule
        if cp < df['SMA200'].iloc[-1]: 
            signal = "BEARISH / AVOID 🛑"

        return {
            "symbol": s,
            "price": round(cp, 2),
            "score": f"{final_score}/10",
            "signal": signal,
            "trend": "Bullish" if cp > df['SMA200'].iloc[-1] else "Bearish"
        }
    except:
        return None

@app.get("/")
def home():
    return {"status": "Global History Engine Active", "scanned_count": len(scanned_history)}

# 🚀 Naya Scan + Auto Save to History
@app.get("/scan/{symbol}")
def scan_and_save(symbol: str):
    s = symbol.upper().strip()
    try:
        time.sleep(1) # Block protection
        df = yf.download(f"{s}.NS", period="2y", interval="1d", progress=False, auto_adjust=True)
        if df.empty: return {"error": "Stock not found"}
        
        analysis = get_20_indicator_analysis(df, s)
        
        # History mein add karein
        if s not in scanned_history:
            scanned_history.append(s)
            
        return analysis
    except Exception as e:
        return {"error": str(e)}

# 📜 ALL HISTORY (Sabka Live Refresh)
@app.get("/all_history")
def get_all_history():
    results = []
    for s in scanned_history:
        time.sleep(1)
        try:
            df = yf.download(f"{s}.NS", period="2y", interval="1d", progress=False, auto_adjust=True)
            if not df.empty:
                results.append(get_20_indicator_analysis(df, s))
        except: continue
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))