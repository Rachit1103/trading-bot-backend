import requests
import pandas as pd
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

RAPID_API_KEY = "3ff3987b04mshdac7fc8bb92c27cp12f7f6jsn11dd6c9ed92e"

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker = f"{s}.NS"
        url = "https://yahoo-finance15.p.rapidapi.com/api/yahoo/hi/history"
        querystring = {"symbol": ticker, "interval": "1d", "diffandsplits": "false"}
        headers = {"X-RapidAPI-Key": RAPID_API_KEY, "X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com"}

        response = requests.get(url, headers=headers, params=querystring).json()
        items = response.get('items', {})
        if not items: return {"symbol": s, "error": "No Data", "score": 0}

        # DataFrame Preparation
        data = [{"Date": d, "Open": float(v['open']), "High": float(v['high']), "Low": float(v['low']), "Close": float(v['close']), "Volume": float(v['volume'])} for d, v in items.items()]
        df = pd.DataFrame(data).sort_values('Date')

        # --- HEAVY INDICATORS LOGIC ---
        # 1. Trend: EMA 20 & SMA 200
        df['EMA20'] = ta.ema(df['Close'], length=20)
        df['SMA200'] = ta.sma(df['Close'], length=200)
        # 2. Momentum: RSI
        df['RSI'] = ta.rsi(df['Close'], length=14)
        # 3. Volatility: Bollinger Bands
        bbands = ta.bbands(df['Close'], length=20, std=2)
        # 4. Strength: ADX
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        # 5. Trend Crossover: MACD
        macd = ta.macd(df['Close'])

        # Latest Values
        cp = df['Close'].iloc[-1]
        rsi = df['RSI'].iloc[-1]
        ema20 = df['EMA20'].iloc[-1]
        sma200 = df['SMA200'].iloc[-1]
        adx_val = adx['ADX_14'].iloc[-1]
        
        # --- SCORING SYSTEM (Out of 10) ---
        score = 0
        if rsi > 40 and rsi < 60: score += 2  # Healthy momentum
        if cp > ema20: score += 2            # Short term uptrend
        if cp > sma200: score += 2           # Long term bullish
        if adx_val > 25: score += 2          # Strong trend strength
        if macd.iloc[-1, 0] > macd.iloc[-1, 2]: score += 2 # Bullish MACD

        return {
            "symbol": ticker,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "adx": round(adx_val, 2),
            "score": score,
            "signal": "STRONG BUY" if score >= 8 else "BUY" if score >= 6 else "NEUTRAL" if score >= 4 else "SELL"
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))