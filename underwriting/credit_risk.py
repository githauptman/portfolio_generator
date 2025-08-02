def estimate_lgd(collateral_quality):
    if collateral_quality == "high":
        return 0.15  # 85% recovery
    elif collateral_quality == "medium":
        return 0.30  # 70% recovery
    else:  # low
        return 0.45  # 55% recovery

def estimate_pd(risk_tier):
    """
    Estimate probability of default based on risk tier.

    Args:
        risk_tier (str): 'strong', 'medium', or 'weak'

    Returns:
        float: Probability of default as a decimal (e.g., 0.02 = 2%)
    """
    pd_mapping = {
        "strong": 0.005,   # 0.5%
        "medium": 0.02,    # 2.0%
        "weak": 0.08       # 8.0%
    }
    return pd_mapping.get(risk_tier, 0.02)  # Default to 2.0% if unknown
