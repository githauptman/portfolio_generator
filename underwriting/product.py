def recommend_loan_type(borrower_profile):
    financials = borrower_profile['financial']
    collateral = borrower_profile['collateral']
    industry_info = borrower_profile['industry']

    # Extract inputs
    revenue = financials.get('revenue', 0)
    ebitda_margin = financials.get('ebitda_margin', 0)
    leverage = financials.get('leverage', 0)
    liquidity = financials.get('liquidity', 0)
    sector = industry_info.get('industry_type', '').lower()

    # Sector-based hints
    revolver_sectors = ['retail', 'distribution', 'wholesale', 'trading', 'agriculture']
    term_loan_sectors = ['manufacturing', 'real estate', 'infrastructure', 'construction']

    # Base loan type from financial ratios
    revolver_score = 0
    term_score = 0

    if liquidity >= 4:
        revolver_score += 1
    if leverage <= 3:
        revolver_score += 1
    if ebitda_margin >= 12:
        revolver_score += 1

    if leverage > 3.5:
        term_score += 1
    if liquidity < 2:
        term_score += 1
    if ebitda_margin < 10:
        term_score += 1

    # Sector modifiers
    if any(keyword in sector for keyword in revolver_sectors):
        revolver_score += 1
    if any(keyword in sector for keyword in term_loan_sectors):
        term_score += 1

    # Determine recommendation
    if revolver_score >= 3 and term_score <= 1:
        return "Revolver"
    elif term_score >= 3 and revolver_score <= 1:
        return "Term Loan"
    elif 2 <= revolver_score <= 3 and 2 <= term_score <= 3:
        return "Hybrid (Term + Revolver)"
    else:
        # Default to hybrid if scoring is ambiguous
        return "Hybrid (Term + Revolver)"
