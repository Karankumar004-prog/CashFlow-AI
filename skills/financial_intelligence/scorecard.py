def compute_health_score(ratios: dict) -> float:
    """
    Computes a deterministic Financial Health Score (0-100) based on four component ratios:
    Savings Rate (25pt), Debt Ratio (25pt), Emergency Runway (25pt), Asset Coverage (25pt).
    """
    # 1. Savings Score Curve (25pt)
    s = ratios.get("savings_rate", 0.0)
    if s >= 0.20:
        savings_score = 25.0
    elif 0.0 <= s < 0.20:
        savings_score = s * 125.0
    else:  # s < 0.0 (net cash flow deficit)
        savings_score = 0.0
        
    # 2. Debt Score Curve (25pt)
    d = ratios.get("debt_ratio", 0.0)
    if d <= 0.15:
        debt_score = 25.0
    elif 0.15 < d <= 0.50:
        debt_score = 25.0 - (((d - 0.15) / 0.35) * 25.0)
    else:  # d > 0.50
        debt_score = 0.0
        
    # 3. Runway Score Curve (25pt)
    r = ratios.get("emergency_runway_months", 0.0)
    if r >= 6.0:
        runway_score = 25.0
    elif 0.0 <= r < 6.0:
        runway_score = (r / 6.0) * 25.0
    else:  # r < 0.0
        runway_score = 0.0
        
    # 4. Asset Score Curve (25pt)
    a = ratios.get("asset_coverage", 999.0)
    if a >= 999.0:  # Represents no liabilities
        asset_score = 25.0
    elif a >= 3.0:
        asset_score = 25.0
    elif 1.0 <= a < 3.0:
        asset_score = ((a - 1.0) / 2.0) * 25.0
    else:  # a < 1.0 (insolvent/negative net worth)
        asset_score = 0.0
        
    total_score = savings_score + debt_score + runway_score + asset_score
    
    # Clamp total score between 0.0 and 100.0
    return max(0.0, min(100.0, total_score))
