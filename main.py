import yfinance as yf
import pandas_ta as ta
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/")
def home():
    return {"status": "AI Trader Pro Backend - 10 Indicator Logic Live"}

@app.get("/scan/{symbol}")
def scan_stock(symbol: str):
    try:
        s = symbol.upper()
        ticker_sym = f"{s}.NS" if not s.endswith(".NS") else s
        
        # Download 6 months data for better Moving Average accuracy
        df = yf.download(ticker_sym, period="6mo", interval="1d", progress=False, threads=False)

        if df.empty or len(df) < 50:
            return {"symbol": symbol, "error": "Insufficient Data", "score": 0}

        # --- 10 INDICATORS CALCULATION ---
        # 1. RSI
        df['RSI'] = ta.rsi(df['Close'], length=14)
        # 2. MACD
        macd = ta.macd(df['Close'])
        # 3. EMA 20 (Short term)
        df['EMA_20'] = ta.ema(df['Close'], length=20)
        # 4. SMA 50 (Medium term)
        df['SMA_50'] = ta.sma(df['Close'], length=50)
        # 5. SMA 200 (Long term)
        df['SMA_200'] = ta.sma(df['Close'], length=200)
        # 6. Bollinger Bands
        bb = ta.bbands(df['Close'], length=20, std=2)
        # 7. ADX (Trend Strength)
        adx = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        # 8. Stochastic Oscillator
        stoch = ta.stoch(df['High'], df['Low'], df['Close'])
        # 9. ATR (Volatility)
        df['ATR'] = ta.atr(df['High'], df['Low'], df['Close'], length=14)
        # 10. Volume MA
        df['VOL_MA'] = ta.sma(df['Volume'], length=20)

        # Current Values
        cp = round(float(df['Close'].iloc[-1]), 2)
        rsi = float(df['RSI'].iloc[-1])
        macd_line = float(macd['MACD_12_26_9'].iloc[-1])
        signal_line = float(macd['MACDs_12_26_9'].iloc[-1])
        ema20 = float(df['EMA_20'].iloc[-1])
        sma50 = float(df['SMA_50'].iloc[-1])
        sma200 = float(df['SMA_200'].iloc[-1])
        adx_val = float(adx['ADX_14'].iloc[-1])
        vol_current = float(df['Volume'].iloc[-1])
        vol_ma = float(df['VOL_MA'].iloc[-1])

        # --- WEIGHTED SCORING LOGIC (Total 10 Points) ---
        score = 0
        if rsi < 40: score += 1.5  # RSI Oversold
        if rsi > 60: score -= 1.0  # RSI Overbought
        if macd_line > signal_line: score += 1.5  # MACD Bullish Crossover
        if cp > ema20: score += 1.0  # Above Short-term Trend
        if cp > sma50: score += 1.0  # Above Medium-term Trend
        if cp > sma200: score += 1.5  # Above Long-term Trend (Golden Zone)
        if adx_val > 25: score += 1.0  # Strong Trend Presence
        if vol_current > vol_ma: score += 1.5  # Volume Confirmation
        if cp < float(bb['BBL_20_2.0'].iloc[-1]): score += 1.0 # Price at Lower Band

        # Final Signal
        signal = "NEUTRAL"
        if score >= 7.5: signal = "STRONG BUY"
        elif score >= 5.5: signal = "BUY"
        elif score <= 3.5: signal = "SELL"

        return {
            "symbol": ticker_sym,
            "current_price": cp,
            "rsi": round(rsi, 2),
            "adx": round(adx_val, 2),
            "signal": signal,
            "score": round(max(0, min(10, score)), 1), # Scale 0-10
            "indicators": {
                "macd": "Bullish" if macd_line > signal_line else "Bearish",
                "trend": "Above 200 SMA" if cp > sma200 else "Below 200 SMA",
                "volume": "High" if vol_current > vol_ma else "Normal"
            }
        }
    except Exception as e:
        return {"error": str(e), "score": 0}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)