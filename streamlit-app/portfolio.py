import yfinance as yf
import pandas as pd
import random

class PortfolioManager:
    def __init__(self):
        # Placeholder tickers
        self.tickers = ["AAPL", "GOOGL", "TSLA", "MSFT", "AMZN", "NVDA", "META", "NFLX", "BABA", "JPM"]

    def get_portfolio(self):
        portfolio = []
        selected_tickers = random.sample(self.tickers, 5)  # Pick 5 random tickers
        for ticker in selected_tickers:
            stock = yf.Ticker(ticker)
            price = stock.info.get("regularMarketPrice", None)
            if price is None:
                continue  # Skip if price isn't available

            holding = {
                "ticker": ticker,
                "quantity": random.randint(10, 100),
                "price_per_stock": round(price, 2),
                "current_value": round(price,2)
            }
            portfolio.append(holding)
        return portfolio

if __name__ == "__main__":
    pm = PortfolioManager()
    portfolio = pm.get_portfolio()

    # Print to console
    for stock in portfolio:
        print(stock)

    # Save to CSV
    df = pd.DataFrame(portfolio)
    df.to_csv("portfolio.csv", index=False)
