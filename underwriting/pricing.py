def price_loan(loan_type, pd, sofr, term_years=None):
    """
    Calculates spread, total rate, and fee structure based on loan type and credit risk.

    Args:
        loan_type (str): One of 'term_loan', 'revolver', 'hybrid'.
        pd (float): Probability of default (e.g., 0.02 for 2%).
        sofr (float): Current SOFR rate (e.g., 5.3).
        term_years (int, optional): Loan term in years.

    Returns:
        dict: Pricing details including spread, total rate, fees.
    """
    # Determine credit tier from PD
    if pd <= 0.005:
        tier = 'strong'
    elif pd <= 0.02:
        tier = 'medium'
    else:
        tier = 'weak'

    # Base spread by tier
    base_spread_bps = {
        'strong': 350,
        'medium': 650,
        'weak': 900
    }[tier]

    # Adjust spreads slightly by product type
    loan_type_adjustment = {
        'term_loan': 0,
        'revolver': 50,
        'hybrid': 75
    }

    spread_bps = base_spread_bps + loan_type_adjustment.get(loan_type, 0)
    total_rate = round(sofr / 100 + spread_bps / 10000, 4)

    # Fee structure by tier
    orig_fee = {
        'strong': 0.75,
        'medium': 1.25,
        'weak': 2.00
    }[tier]

    unused_fee = {
        'strong': 0.50,
        'medium': 0.75,
        'weak': 1.00
    }[tier]

    return {
        "loan_type": loan_type,
        "risk_tier": tier,
        "spread_bps": spread_bps,
        "total_rate": total_rate,
        "origination_fee_pct": orig_fee,
        "unused_fee_pct": unused_fee if loan_type in ["revolver", "hybrid"] else 0.0,
        "term_years": term_years
    }
