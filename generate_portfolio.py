#!/usr/bin/env python3
"""
Generate portfolio data for FinSeek AI
"""
import sys
import os

# Add the portfolio directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'portfolio'))

from portfolio.portfolio import PortfolioManager

def main():
    print("🤑 FinSeek AI - Generating Portfolio Data...")
    
    try:
        pm = PortfolioManager()
        portfolio = pm.get_portfolio()
        
        if not portfolio:
            print("❌ Failed to generate portfolio data")
            return False
            
        # Save to multiple locations
        pm.save_portfolio_csv(portfolio, "portfolio.csv")
        pm.save_portfolio_csv(portfolio, "streamlit-app/portfolio.csv")
        
        print(f"✅ Generated portfolio with {len(portfolio)} holdings:")
        total_value = sum(holding['current_value'] for holding in portfolio)
        
        for holding in portfolio:
            allocation = (holding['current_value'] / total_value) * 100
            print(f"  • {holding['ticker']}: ${holding['current_value']:,.2f} ({allocation:.1f}%)")
            
        print(f"\n💰 Total Portfolio Value: ${total_value:,.2f}")
        print("📁 Saved to: portfolio.csv and streamlit-app/portfolio.csv")
        return True
        
    except Exception as e:
        print(f"❌ Error generating portfolio: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 