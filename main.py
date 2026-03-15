from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from core.scanner import calculate_master_score

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.get("/scan/{ticker}")
async def scan_stock(ticker: str):
    # Direct calling the score logic
    return calculate_master_score(ticker)

if __name__ == "__main__":
    # 0.0.0.0 is crucial for mobile connection
    uvicorn.run(app, host="0.0.0.0", port=8000)