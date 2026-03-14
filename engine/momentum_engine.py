def calculate_momentum_score(price_change_pct: float, volume_ratio: float) -> float:
    """
    Calculate a normalized momentum score.
    Higher price change + higher volume ratio = higher score.
    """
    # Clip extreme values to prevent unbounded scores
    # Max considered price change is 10%, max volume ratio is 5x
    clpd_price_change = max(min(price_change_pct, 10.0), -10.0) / 10.0 # -1 to 1
    
    # Normalize volume ratio (1 is normal, bounded to 0-1 range for impact)
    # If volume is 5x normal, it's a huge spike. 
    norm_volume = min(volume_ratio, 5.0) / 5.0 
    
    # Weights
    score = (clpd_price_change * 0.6) + (norm_volume * 0.4)
    
    # Scale to -1 to 1 for consistency with sentiment
    return max(min(score, 1.0), -1.0)

def evaluate_momentum(market_data: dict) -> dict:
    """
    Evaluate market data and attach a momentum score.
    """
    if not market_data:
        return {"momentum_score": 0.0, "status": "Neutral"}
        
    score = calculate_momentum_score(
        market_data.get("price_change_pct", 0), 
        market_data.get("volume_ratio", 1.0)
    )
    
    status = "Neutral"
    if score > 0.4:
        status = "Strong"
    elif score > 0.1:
        status = "Rising"
    elif score < -0.4:
        status = "Crashing"
    elif score < -0.1:
        status = "Falling"
        
    return {
        "momentum_score": score,
        "momentum_status": status
    }

if __name__ == "__main__":
    print(calculate_momentum_score(5.0, 3.0))
