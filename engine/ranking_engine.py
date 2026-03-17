def rank_signals(signals: list) -> list:
    """
    Sort stocks by score.
    """
    # Sort descending by score
    return sorted(signals, key=lambda x: x.get("score", 0), reverse=True)

if __name__ == "__main__":
    test_signals = [
        {"ticker": "NVDA", "score": 89},
        {"ticker": "AAPL", "score": 45},
        {"ticker": "AMD", "score": 84}
    ]
    print(rank_signals(test_signals))
