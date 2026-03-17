import pandas as pd
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import requests
import io
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🛡️ Yeh Headers Yahoo ko lagega ki aap Chrome browser use kar rahe ho
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}

@app.get("/")
def home():
    return {"status": "Anti-Block Engine Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper().strip()
        # Stooq is currently the most stable free source for Indian Stocks
        ticker = f"{s}.IN"
        url = f"https://stooq.com/q/d/l/?s={ticker}&i=d"
        
        # Request with fake browser identity
        response = requests.get(url, headers=HEADERS, timeout=10)
        
        if response.status_code != 200:
            return {"symbol": s, "error": "Server busy, try again", "score": 0}

        df = pd.read_csv(io.StringIO(response.text))

        if df.empty or len(df) < 200:
            return {"symbol": s, "error": "Symbol not found or low history", "score": 0}

        # Cleaning columns
        df.columns = [c.capitalize() for c in df.columns]

        # 🚀 HEAVY ANALYSIS LOGIC (Professional Grade)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])

        # Latest Values
        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        ema20 = float(df['EMA20'].iloc[-1])
        sma200 = float(df['SMA200'].iloc[-1])
        
        # MACD Signal Line
        macd_val = macd.iloc[-1, 0]
        signal_val = macd.iloc[-1, 2]

        # 📊 SCORING SYSTEM (High Accuracy)
        score = 0
        if cp > sma200: score += 4  # Golden Trend Rule
        if cp > ema20: score += 2   # Short term strength
        if 40 < rsi < 65: score += 2 # Momentum
        if macd_val > signal_val: score += 2 # Trend Reversal

        return {
            "symbol": s,
            "current_price": round(cp, 2),
            "score": score,
            "rsi": round(rsi, 2),
            "trend": "Strong Bullish" if cp > sma200 else "Bearish",
            "signal": "STRONG BUY 🚀" if score >= 8 else "BUY ✅" if score >= 5 else "WAIT ⏳"
        }

    except Exception as e:
        return {"error": "System Cooling...", "details": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))