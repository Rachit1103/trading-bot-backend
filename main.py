import requests
import pandas as pd
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# AAPKI TWELVE DATA API KEY
API_KEY = "bac6342d248e44c0849209d9bec85e3e"

@app.get("/")
def home():
    return {"status": "Twelve Data Professional Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        # Twelve Data URL - Daily Time Series
        # India stocks ke liye symbol like 'RELIANCE:NSE' ya 'TCS:NSE'
        market_symbol = f"{s}:NSE"
        url = f"https://api.twelvedata.com/time_series?symbol={market_symbol}&interval=1day&outputsize=100&apikey={API_KEY}"
        
        response = requests.get(url).json()

        if "values" not in response:
            return {"symbol": s, "error": response.get("message", "API Error"), "score": 0}

        # Data Formatting
        df = pd.DataFrame(response["values"])
        df["close"] = df["close"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        
        # Reverse because Twelve Data gives newest first
        df = df.iloc[::-1].reset_index(drop=True)

        # 🛠️ INDICATORS LOGIC
        # 1. RSI
        df['RSI'] = ta.rsi(df['close'], length=14)
        # 2. EMA 20
        df['EMA20'] = ta.ema(df['close'], length=20)
        # 3. MACD
        macd = ta.macd(df['close'])

        # Latest Values
        cp = float(df['close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1]) if not df['RSI'].empty else 50
        ema20 = float(df['EMA20'].iloc[-1]) if not df['EMA20'].empty else cp
        
        # Scoring Logic
        score = 0
        if rsi < 40: score += 3 # Oversold
        if cp > ema20: score += 4 # Uptrend
        if not macd.empty and macd.iloc[-1, 0] > macd.iloc[-1, 2]: score += 3 # Bullish Crossover

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": score,
            "signal": "STRONG BUY" if score >= 8 else "BUY" if score >= 6 else "WAIT"
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)