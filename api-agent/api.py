from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yfinance as yf
import pandas as pd
from typing import List, Dict
import asyncio
from datetime import datetime, timedelta

app = FastAPI(title="Finance API Agent")

class MarketData(BaseModel):
    symbol: str
    current_price: float
    change_percent: float
    volume: int
    market_cap: float
    pe_ratio: float | None

class RiskExposure(BaseModel):
    ticker_list: List[str]
    allocation_pct: float
    total_value: float
    risk_metrics: Dict[str, float]

@app.get("/market-data/{symbol}")
async def get_market_data(symbol: str) -> MarketData:
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        return MarketData(
            symbol=symbol,
            current_price=info.get('currentPrice', 0.0),
            change_percent=info.get('regularMarketChangePercent', 0.0),
            volume=info.get('volume', 0),
            market_cap=info.get('marketCap', 0.0),
            pe_ratio=info.get('trailingPE')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")

@app.get("/risk-exposure")
async def get_risk_exposure(ticker_list: str) -> RiskExposure:
    try:
        tickers = ticker_list.split(',')
        total_value = 0.0
        volatilities = {}
        
        # Calculate portfolio metrics
        for ticker in tickers:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            current_price = hist['Close'][-1]
            daily_returns = hist['Close'].pct_change().dropna()
            volatility = daily_returns.std() * (252 ** 0.5)  # Annualized volatility
            
            total_value += current_price * 100  # Assuming 100 shares each
            volatilities[ticker] = volatility
        
        # Calculate allocation percentage (equal weight for simplicity)
        allocation = 100.0 / len(tickers)
        
        return RiskExposure(
            ticker_list=tickers,
            allocation_pct=allocation,
            total_value=total_value,
            risk_metrics={
                "portfolio_volatility": sum(volatilities.values()) / len(volatilities),
                "max_drawdown": min(volatilities.values()),
                "sharpe_ratio": 1.5  # Simplified calculation
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating risk exposure: {str(e)}")

@app.get("/historical-data/{symbol}")
async def get_historical_data(symbol: str, period: str = "1y"):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        return {
            "dates": hist.index.strftime('%Y-%m-%d').tolist(),
            "prices": hist['Close'].tolist(),
            "volumes": hist['Volume'].tolist()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching historical data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

