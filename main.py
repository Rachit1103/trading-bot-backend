import requests
import pandas as pd
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 🔑 AAPKI RAPIDAPI KEY
RAPID_API_KEY = "3ff3987b04mshdac7fc8bb92c27cp12f7f6jsn11dd6c9ed92e"

@app.get("/")
def home():
    return {"status": "RapidAPI Pro Backend Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker = f"{s}.NS"
        
        # Sahi Endpoint for yahoo-finance15
        url = "https://yahoo-finance15.p.rapidapi.com/api/yahoo/hi/history"
        querystring = {"symbol": ticker, "interval": "1d", "diffandsplits": "false"}
        
        headers = {
            "X-RapidAPI-Key": RAPID_API_KEY,
            "X-RapidAPI-Host": "yahoo-finance15.p.rapidapi.com"
        }

        response = requests.get(url, headers=headers, params=querystring).json()
        
        # Items extract karein
        items = response.get('items', {})
        if not items:
            return {"symbol": s, "error": "No Data Found", "score": 0}

        # Convert dictionary to DataFrame for calculation
        data_list = []
        for date, val in items.items():
            data_list.append({"Date": date, "Close": float(val['close'])})
        
        df = pd.DataFrame(data_list)
        df = df.sort_values('Date') 

        # Indicators Calculation
        df['RSI'] = ta.rsi(df['Close'], length=14)
        df['EMA20'] = ta.ema(df['Close'], length=20)

        cp = float(df['Close'].iloc[-1])
        rsi = float(df['RSI'].iloc[-1]) if not df['RSI'].empty else 50
        ema20 = float(df['EMA20'].iloc[-1]) if not df['EMA20'].empty else cp

        # AI Scoring Logic
        score = 0
        if rsi < 45: score += 5
        if cp > ema20: score += 5

        return {
            "symbol": ticker,
            "current_price": round(cp, 2),
            "rsi": round(rsi, 2),
            "score": score,
            "signal": "BUY" if score >= 7 else "WAIT"
        }
    except Exception as e:
        return {"error": "API Connection Busy", "score": 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))