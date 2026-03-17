import os
import time
from data.news_fetcher import fetch_company_news
from data.market_fetcher import fetch_market_data
from engine.signal_generator import generate_signal
from engine.ranking_engine import rank_signals
from database.db import save_signal, init_db
from alerts.telegram_alerts import send_alert, format_signal_alert

WATCHLIST = ["NVDA", "AAPL", "AMD", "TSLA", "MSFT"]
SCORE_THRESHOLD = 45

def run_workflow():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Starting signal engine...")
    init_db()
    raw_signals = []
    
    for ticker in WATCHLIST:
        print(f"Analyzing {ticker}...")
        
        # 1. Fetch Market Data
        market_data = fetch_market_data(ticker)
        
        # 2. Fetch News
        news_data = fetch_company_news(ticker)
        
        # 3. Generate Signal
        signal = generate_signal(ticker, news_data, market_data)
        raw_signals.append(signal)
        
    # 4. Rank Signals
    ranked_signals = rank_signals(raw_signals)
    
    print("\nTop Opportunities:")
    for sig in ranked_signals:
        print(f"{sig['ticker']} - Score: {sig['score']} | Momentum: {sig['momentum_status']} | Sentiment: {sig['sentiment_status']}")
        
        # 5. Store Signals
        save_signal(sig)
        
        # 6. Send Alerts
        if sig['score'] >= SCORE_THRESHOLD:
            msg = format_signal_alert(sig)
            send_alert(msg)

    print("\nWorkflow complete.")

if __name__ == "__main__":
    print("Starting AI Trading Brain in Background Mode...")
    print("The system will scan for signals every 10 minutes.")
    
    while True:
        try:
            run_workflow()
        except Exception as e:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error during workflow: {e}")
        
        # Sleep for 10 minutes (600 seconds)
        print("Sleeping for 10 minutes...\n")
        time.sleep(600)
