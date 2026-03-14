import yfinance as yf
import pandas as pd

def fetch_market_data(ticker: str, period="5d"):
    """
    Fetch recent market data for a ticker using yfinance.
    Calculates simple momentum indicators.
    """
    try:
        stock = yf.Ticker(ticker)
        # Fetch daily data
        df = stock.history(period=period)
        
        if df.empty or len(df) < 2:
            return None
            
        # Current and previous close
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        
        # Price change
        price_change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # Volume
        current_volume = df['Volume'].iloc[-1]
        avg_volume = df['Volume'].mean()
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        return {
            "ticker": ticker,
            "current_price": float(current_price),
            "prev_price": float(prev_price),
            "price_change_pct": float(price_change_pct),
            "current_volume": int(current_volume),
            "volume_ratio": float(volume_ratio),
            "timestamp": df.index[-1].isoformat()
        }
    except Exception as e:
        print(f"Error fetching market data for {ticker}: {e}")
        return None

if __name__ == "__main__":
    print(fetch_market_data("AAPL"))
