import requests
import pandas as pd
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🔑 APNI RAPIDAPI KEY YAHAN DALEN
RAPID_API_KEY = "3ff3987b04mshdac7fc8bb92c27cp12f7f6jsn11dd6c9ed92e"

@app.get("/")
def home():
    return {"status": "AI Trading Pro Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker = f"{s}.NS"
        
        # Sahi Endpoint for High Accuracy Data
        url = "https://yh-finance.p.rapidapi.com/stock/v3/get-chart"
        querystring = {"interval":"1d","symbol":ticker,"range":"2y","region":"IN"}
        headers = {
            "X-RapidAPI-Key": RAPID_API_KEY,
            "X-RapidAPI-Host": "yh-finance.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring).json()
        
        # Data Extraction logic
        result = response.get('chart', {}).get('result', [None])[0]
        if not result:
            return {"symbol": s, "error": "Symbol Not Found", "score": 0}

        prices = result['indicators']['quote'][0]['close']
        df = pd.DataFrame({"Close": prices}).dropna()

        if len(df) < 200:
            return {"symbol": s, "error": "Insufficient history for SMA 200", "score": 0}

        # --- HEAVY INDICATORS CALCULATION ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        macd = ta.macd(df['Close'])
        bbands = ta.bbands(df['Close'], length=20, std=2)

        # Latest Values
        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1])
        ema20 = float(df['EMA20'].iloc[-1])
        sma200 = float(df['SMA200'].iloc[-1])
        macd_line = float(macd.iloc[-1, 0])
        signal_line = float(macd.iloc[-1, 2])
        lower_band = float(bbands.iloc[-1, 0])

        # --- ACCURACY SCORING SYSTEM (Out of 10) ---
        score = 0
        if rsi < 35: score += 2 # Oversold (Buy Opportunity)
        if cp > ema20: score += 2 # Short-term momentum
        if cp > sma200: score += 2 # Long-term Bullish Trend
        if macd_line > signal_line: score += 2 # Bullish Crossover
        if cp < lower_band * 1.02: score += 2 # Near Support

        return {
            "symbol": ticker,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "trend": "Bullish" if cp > sma200 else "Bearish",
            "score": score,
            "signal": "STRONG BUY 🚀" if score >= 8 else "BUY ✅" if score >= 6 else "WAIT ⏳"
        }
    except Exception as e:
        return {"error": "API Error", "details": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))