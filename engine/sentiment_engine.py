from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def analyze_sentiment(text: str) -> float:
    """
    Analyze sentiment of text using VADER.
    Returns a score between -1 (bearish) and 1 (bullish).
    """
    if not text:
        return 0.0
        
    analyzer = SentimentIntensityAnalyzer()
    
    # vader returns a dictionary with pos, neu, neg, and compound scores
    # compound is normalized, between -1 and +1
    scores = analyzer.polarity_scores(text)
    
    return scores['compound']

def aggregate_news_sentiment(news_items: list) -> float:
    """
    Calculate average sentiment score from a list of news items.
    """
    if not news_items:
        return 0.0
        
    total_score = 0
    for item in news_items:
        text = f"{item.get('headline', '')} {item.get('summary', '')}"
        total_score += analyze_sentiment(text)
        
    return total_score / len(news_items)

if __name__ == "__main__":
    text = "Nvidia sees massive earnings beat, raises guidance significantly"
    print(f"Sentiment for '{text}': {analyze_sentiment(text)}")
