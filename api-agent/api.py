from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict
import requests
import os
from datetime import datetime
from enum import Enum

app = FastAPI(title="Historical Market Data API")

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")  # 'demo' works for limited testing

class TimeFrame(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    INTRADAY = "intraday"

class HistoricalDataPoint(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    dividend: Optional[float] = None
    split_coefficient: Optional[float] = None

class HistoricalDataResponse(BaseModel):
    symbol: str
    timeframe: TimeFrame
    data_points: List[HistoricalDataPoint]
    metadata: Dict[str, str]

def get_alpha_vantage_historical_data(
    symbol: str,
    timeframe: TimeFrame = TimeFrame.DAILY,
    output_size: str = "compact",
    adjusted: bool = True
) -> Dict:
    """Get historical data from Alpha Vantage with proper error handling"""
    function_map = {
        TimeFrame.DAILY: "TIME_SERIES_DAILY_ADJUSTED" if adjusted else "TIME_SERIES_DAILY",
        TimeFrame.WEEKLY: "TIME_SERIES_WEEKLY_ADJUSTED",
        TimeFrame.MONTHLY: "TIME_SERIES_MONTHLY_ADJUSTED",
        TimeFrame.INTRADAY: "TIME_SERIES_INTRADAY"
    }
    
    params = {
        "function": function_map[timeframe],
        "symbol": symbol,
        "apikey": ALPHA_VANTAGE_API_KEY,
        "outputsize": output_size
    }
    
    if timeframe == TimeFrame.INTRADAY:
        params["interval"] = "60min"  # Default to 60min intervals
    
    try:
        response = requests.get("https://www.alphavantage.co/query", params=params)
        response.raise_for_status()
        data = response.json()
        
        if "Error Message" in data:
            raise ValueError(data["Error Message"])
        if "Note" in data:  # Rate limit message
            raise ValueError(data["Note"])
        
        return data
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=502, detail=f"API request failed: {str(e)}")

def parse_historical_data(raw_data: Dict, timeframe: TimeFrame) -> Dict:
    """Parse Alpha Vantage response into standardized format"""
    # Find the time series key (differs by endpoint)
    time_series_key = next(
        (k for k in raw_data.keys() 
         if "Time Series" in k or "Stock Quotes" in k),
        None
    )
    
    if not time_series_key:
        raise ValueError("No time series data found in API response")
    
    metadata = raw_data.get("Meta Data", {})
    time_series = raw_data[time_series_key]
    
    data_points = []
    for date_str, values in time_series.items():
        try:
            point = {
                "date": date_str,
                "open": float(values.get("1. open", values.get("open", 0))),
                "high": float(values.get("2. high", values.get("high", 0))),
                "low": float(values.get("3. low", values.get("low", 0))),
                "close": float(values.get("4. close", values.get("close", 0))),
                "volume": int(values.get("5. volume", values.get("volume", 0)))
            }
            
            # Add adjusted close if available
            if "5. adjusted close" in values:
                point["adjusted_close"] = float(values["5. adjusted close"])
            if "7. dividend amount" in values:
                point["dividend"] = float(values["7. dividend amount"])
            if "8. split coefficient" in values:
                point["split_coefficient"] = float(values["8. split coefficient"])
            
            data_points.append(point)
        except (ValueError, AttributeError) as e:
            continue  # Skip malformed data points
    
    if not data_points:
        raise ValueError("No valid data points found in response")
    
    return {
        "metadata": metadata,
        "data_points": sorted(data_points, key=lambda x: x["date"], reverse=True)
    }

@app.get("/historical-data/{symbol}", response_model=HistoricalDataResponse)
async def get_historical_data(
    symbol: str,
    timeframe: TimeFrame = TimeFrame.DAILY,
    output_size: str = Query("compact", regex="^(compact|full)$"),
    adjusted: bool = True
):
    try:
        raw_data = get_alpha_vantage_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            output_size=output_size,
            adjusted=adjusted
        )
        
        parsed_data = parse_historical_data(raw_data, timeframe)
        
        return HistoricalDataResponse(
            symbol=symbol,
            timeframe=timeframe,
            data_points=[HistoricalDataPoint(**dp) for dp in parsed_data["data_points"]],
            metadata=parsed_data["metadata"]
        )
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing data: {str(e)}")

@app.get("/historical-data/range/{symbol}", response_model=HistoricalDataResponse)
async def get_historical_data_range(
    symbol: str,
    start_date: str,
    end_date: str = datetime.now().strftime("%Y-%m-%d"),
    timeframe: TimeFrame = TimeFrame.DAILY,
    adjusted: bool = True
):
    try:
        # First get all historical data
        response = await get_historical_data(
            symbol=symbol,
            timeframe=timeframe,
            output_size="full",
            adjusted=adjusted
        )
        
        # Filter by date range
        filtered_points = [
            point for point in response.data_points
            if start_date <= point.date <= end_date
        ]
        
        if not filtered_points:
            raise ValueError(f"No data found between {start_date} and {end_date}")
        
        return HistoricalDataResponse(
            symbol=response.symbol,
            timeframe=response.timeframe,
            data_points=filtered_points,
            metadata=response.metadata
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)