import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY", "")

def fetch_company_news(ticker: str, days: int = 3):
    """Fetch recent news for a specific ticker using Finnhub."""
    if not FINNHUB_API_KEY:
        print("Warning: FINNHUB_API_KEY is not set.")
        return []

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    start_str = start_date.strftime("%Y-%m-%d")
    end_str = end_date.strftime("%Y-%m-%d")

    url = f"https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker,
        "from": start_str,
        "to": end_str,
        "token": FINNHUB_API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        news = []
        for item in data[:10]: # Limit to top 10
            news.append({
                "ticker": ticker,
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "timestamp": datetime.fromtimestamp(item.get("datetime", 0)).isoformat()
            })
        return news
    except Exception as e:
        print(f"Error fetching news for {ticker}: {e}")
        return []

def fetch_general_market_news():
    """Fetch general market news."""
    if not FINNHUB_API_KEY:
        return []

    url = f"https://finnhub.io/api/v1/news"
    params = {
        "category": "general",
        "token": FINNHUB_API_KEY
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        news = []
        for item in data[:20]:
            news.append({
                "headline": item.get("headline", ""),
                "summary": item.get("summary", ""),
                "source": item.get("source", ""),
                "timestamp": datetime.fromtimestamp(item.get("datetime", 0)).isoformat()
            })
        return news
    except Exception as e:
        print(f"Error fetching general news: {e}")
        return []

if __name__ == "__main__":
    print(fetch_company_news("AAPL", days=1))
