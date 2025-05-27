from fastapi import FastAPI, HTTPException
import requests

app = FastAPI(title="Simplified Scraper Agent")

@app.get("/earnings-surprise")
async def earnings_surprise(symbol: str):
    """
    GET /earnings-surprise?symbol=TSM
    Fetches the latest EPS actual vs estimate via Yahoo Finance JSON API
    and returns the surprise percentage.
    """
    url = f"https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    params = {"modules": "earningsHistory"}
    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(url, params=params, headers=headers)
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch data from Yahoo Finance")

    data = resp.json()
    try:
        hist = data['quoteSummary']['result'][0]['earningsHistory']['history'][0]
        actual = hist['epsActual']['raw']
        estimate = hist['epsEstimate']['raw']
    except (KeyError, IndexError, TypeError):
        raise HTTPException(status_code=404, detail="Earnings data not available for symbol")

    surprise = (actual - estimate) / estimate * 100 if estimate else 0.0
    return {"symbol": symbol, "surprise_pct": round(surprise, 2)}
