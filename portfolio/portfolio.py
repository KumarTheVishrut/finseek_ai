import yfinance as yf
import pandas as pd
import random
import os

class PortfolioManager:
    def __init__(self):
        # Asia tech focus tickers
        self.tickers = [
            "2330.TW",  # TSMC
            "005930.KS",  # Samsung
            "9988.HK",  # Alibaba
            "ASML",  # ASML
            "TSM",  # TSMC ADR
            "BABA",  # Alibaba ADR
            "NVDA",  # NVIDIA
            "AAPL",  # Apple
            "GOOGL",  # Google
            "MSFT"  # Microsoft
        ]

    def get_portfolio(self):
        portfolio = []
        selected_tickers = random.sample(self.tickers, 6)  # Pick 6 random tickers
        
        for ticker in selected_tickers:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                price = info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose")
                
                if price is None:
                    # Fallback to historical data
                    hist = stock.history(period="1d")
                    if not hist.empty:
                        price = hist['Close'].iloc[-1]
                    else:
                        continue

                quantity = random.randint(10, 100)
                current_value = round(price * quantity, 2)
                
                holding = {
                    "ticker": ticker,
                    "quantity": quantity,
                    "price_per_stock": round(price, 2),
                    "current_value": current_value
                }
                portfolio.append(holding)
                
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                continue
                
        return portfolio

    def save_portfolio_csv(self, portfolio, filename="portfolio.csv"):
        """Save portfolio to CSV file"""
        df = pd.DataFrame(portfolio)
        df.to_csv(filename, index=False)
        return filename

if __name__ == "__main__":
    pm = PortfolioManager()
    portfolio = pm.get_portfolio()

    # Print to console
    print("Generated Portfolio:")
    for stock in portfolio:
        print(f"{stock['ticker']}: {stock['quantity']} shares @ ${stock['price_per_stock']} = ${stock['current_value']}")

    # Save to multiple locations for different services
    pm.save_portfolio_csv(portfolio, "portfolio.csv")
    pm.save_portfolio_csv(portfolio, "streamlit-app/portfolio.csv")
    
    print(f"\nPortfolio saved to portfolio.csv and streamlit-app/portfolio.csv") 