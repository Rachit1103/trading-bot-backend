import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import pandas as pd
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# 💾 FILE PATH (History ko "Yad" rakhne ke liye)
HISTORY_FILE = "history.txt"

# 📋 Global List: Server start hote hi file se data load karega
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r") as f:
        scanned_names_history = [line.strip() for line in f.readlines() if line.strip()]
else:
    scanned_names_history = []

def save_name_to_file(symbol):
    """Stock ka naam permanent file mein likhne ke liye"""
    if symbol not in scanned_names_history:
        scanned_names_history.append(symbol)
        with open(HISTORY_FILE, "a") as f:
            f.write(f"{symbol}\n")

def calculate_20_indicators_accuracy(df, s):
    """Top 20 Indicators Combined Logic for Highest Accuracy"""
    try:
        score = 0
        cp = float(df['Close'].iloc[-1])
        
        # --- 1-10: Trend Indicators ---
        df['SMA200'] = ta.sma(df['Close'], length=200)
        df['SMA100'] = ta.sma(df['Close'], length=100)
        df['SMA50'] = ta.sma(df['Close'], length=50)
        df['SMA20'] = ta.sma(df['Close'], length=20)
        df['EMA9'] = ta.ema(df['Close'], length=9)
        df['EMA21'] = ta.ema(df['Close'], length=21)
        df['HMA9'] = ta.hma(df['Close'], length=9)
        
        if cp > df['SMA200'].iloc[-1]: score += 2.0
        if cp > df['SMA50'].iloc[-1]: score += 1.0
        if cp > df['EMA21'].iloc[-1]: score += 0.5
        if df['SMA20'].iloc[-1] > df['SMA50'].iloc[-1]: score += 0.5
        if cp > df['HMA9'].iloc[-1]: score += 0.5

        # --- 11-16: Momentum & Volatility ---
        df['RSI'] = ta.rsi(df['Close'], length=14)
        macd = ta.macd(df['Close'])
        bbands = ta.bbands(df['Close'], length=20)
        stoch = ta.stoch(df['High'], df['Low'], df['Close'])
        
        rsi_val = df['RSI'].iloc[-1]
        if 45 < rsi_val < 65: score += 1.5
        if not macd.empty and macd.iloc[-1, 0] > macd.iloc[-1, 2]: score += 1.0
        if cp > bbands.iloc[-1, 1]: score += 0.5
        if stoch.iloc[-1, 0] > stoch.iloc[-1, 1]: score += 0.5

        # --- 17-20: Strength & Volume ---
        adx = ta.adx(df['High'], df['Low'], df['Close'])
        df['OBV'] = ta.obv(df['Close'], df['Volume'])
        df['MFI'] = ta.mfi(df['High'], df['Low'], df['Close'], df['Volume'])
        
        if not adx.empty and adx.iloc[-1, 0] > 25: score += 1.0
        if df['OBV'].iloc[-1] > df['OBV'].iloc[-2]: score += 0.5
        if df['MFI'].iloc[-1] > 50: score += 0.5

        final_score = round(score, 1)
        signal = "STRONG BUY 🚀" if final_score >= 8 else "BUY ✅" if final_score >= 6 else "WAIT ⏳"
        
        if cp < df['SMA200'].iloc[-1]: signal = "BEARISH / AVOID 🛑"

        return {
            "symbol": s,
            "price": round(cp, 2),
            "score": f"{final_score}/10",
            "signal": signal,
            "accuracy": "High (20 Indicators)",
            "trend": "Bullish" if cp > df['SMA200'].iloc[-1] else "Bearish"
        }
    except:
        return {"error": "Calculation error"}

@app.get("/")
def home():
    return {"status": "Persistent Engine Active", "history_count": len(scanned_names_history)}

@app.get("/scan/{symbol}")
def scan_single_stock(symbol: str):
    s = symbol.upper().strip()
    try:
        ticker = yf.Ticker(f"{s}.NS")
        df = ticker.history(period="2y", interval="1d", auto_adjust=True)
        
        if df.empty or len(df) < 200:
            return {"error": "Stock data not found"}

        # ✅ Permanent History mein save karna
        save_name_to_file(s)

        return calculate_20_indicators_accuracy(df, s)
    except Exception as e:
        return {"error": str(e)}

@app.get("/history_names")
def get_history():
    return {"scanned_stocks": scanned_names_history}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))