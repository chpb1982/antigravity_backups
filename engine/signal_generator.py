from engine.sentiment_engine import aggregate_news_sentiment
from engine.momentum_engine import evaluate_momentum

def generate_signal(ticker: str, news_data: list, market_data: dict) -> dict:
    """
    Combine sentiment, momentum, and volume into a final opportunity score.
    """
    sentiment_score = aggregate_news_sentiment(news_data)
    momentum_data = evaluate_momentum(market_data)
    
    momentum_score = momentum_data.get("momentum_score", 0.0)
    momentum_status = momentum_data.get("momentum_status", "Neutral")
    
    # Scale from -1..1 to 0..100
    # Base score of 50 (neutral)
    
    opportunity_score = (
        (sentiment_score * 0.4) +
        (momentum_score * 0.6)
    )
    
    # Map from [-1.0, 1.0] to [0, 100]
    final_score = int(((opportunity_score + 1.0) / 2.0) * 100)
    
    sentiment_status = "Bullish" if sentiment_score > 0.2 else ("Bearish" if sentiment_score < -0.2 else "Neutral")
    
    return {
        "ticker": ticker,
        "score": final_score,
        "sentiment": round(sentiment_score, 2),
        "sentiment_status": sentiment_status,
        "momentum": round(momentum_score, 2),
        "momentum_status": momentum_status,
        "volume_ratio": round(market_data.get("volume_ratio", 1.0), 2) if market_data else 1.0,
        "price_change_pct": round(market_data.get("price_change_pct", 0.0), 2) if market_data else 0.0
    }
