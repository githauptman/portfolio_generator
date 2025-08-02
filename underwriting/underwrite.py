import json
from .credit_risk import estimate_lgd, estimate_pd
from .facility_size import recommend_facility_size
from .product import recommend_loan_type
from .term_generator import recommend_loan_term
from .pricing import price_loan

def underwrite_loan_profile(profile, sofr):
    """
    Underwrites a loan based on borrower profile and current SOFR.

    Args:
        profile (dict): Borrower profile with financial, collateral, management, industry info.
        sofr (float): Current SOFR rate (percentage, e.g. 5.3).

    Returns:
        dict: Underwriting output with credit metrics, pricing, and loan terms.
    """
    # Estimate key credit metrics
    pd = estimate_pd(profile["financial"]["credit_strength"])
    lgd = estimate_lgd(profile["collateral"]["collateral_quality"])
    facility_size = recommend_facility_size(profile["financial"])
    loan_type = recommend_loan_type(profile)
    term_years = recommend_loan_term(profile, loan_type)

    # Calculate pricing based on loan type, PD, SOFR, and term
    pricing = price_loan(loan_type, pd, sofr, term_years)

    # Assemble final output
    result = {
        "credit_metrics": {
            "probability_of_default": pd,
            "loss_given_default": lgd,
            "facility_size": facility_size,
            "loan_type": loan_type,
            "term_years": term_years,
        },
        "pricing": pricing,
        "borrower_profile": profile
    }

    return result

def pretty_print_underwriting(result):
    print("=== Credit Metrics ===")
    for k, v in result['credit_metrics'].items():
        print(f"{k.replace('_', ' ').title()}: {v}")

    print("\n=== Pricing ===")
    for k, v in result['pricing'].items():
        if isinstance(v, float):
            print(f"{k.replace('_', ' ').title()}: {v:.4f}")
        else:
            print(f"{k.replace('_', ' ').title()}: {v}")

    print("\n=== Borrower Information ===")
    borrower_profile = result['borrower_profile']
    borrower_id = borrower_profile.get('borrower_id', 'N/A')
    print(f"Borrower ID: {borrower_id}")

    print("\n=== Full Borrower Profile ===")
    # Pretty-print borrower profile as indented JSON for clarity
    print(json.dumps(borrower_profile, indent=4))
