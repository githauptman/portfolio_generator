def recommend_facility_size(financial_profile, target_leverage=4.5):
    """
    Recommend a facility size based on current leverage and revenue.
    
    Args:
        financial_profile (dict): contains revenue, ebitda_margin, leverage.
        target_leverage (float): max desired leverage ratio after facility.
        
    Returns:
        float: recommended facility size (debt increase allowed).
    """
    revenue = financial_profile["revenue"]
    ebitda_margin = financial_profile["ebitda_margin"] / 100  # convert % to decimal
    current_leverage = financial_profile["leverage"]
    
    # Estimate EBITDA
    ebitda = revenue * ebitda_margin
    
    # Current debt (Debt = Leverage * EBITDA)
    current_debt = current_leverage * ebitda
    
    # Max allowed debt for target leverage
    max_debt = target_leverage * ebitda
    
    # Recommended new facility size = difference between max allowed and current debt
    recommended_facility = max(0, max_debt - current_debt)
    
    return recommended_facility
