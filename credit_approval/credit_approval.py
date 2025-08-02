def credit_approval_with_portfolio(underwriting_output, portfolio):
    borrower_id = underwriting_output['borrower_profile']['borrower_id']
    industry = underwriting_output['borrower_profile']['industry']['industry']
    facility_size = underwriting_output['credit_metrics']['facility_size']

    # Exposure checks
    industry_total = portfolio['industry_exposure'].get(industry, 0)
    borrower_total = portfolio['borrower_exposure'].get(borrower_id, 0)

    # Capacity checks
    available_capacity = portfolio['max_capacity'] - portfolio['used_capacity']

    if facility_size > available_capacity:
        return {
            "decision": "Declined",
            "reason": "Insufficient portfolio capacity",
            "facility_size": facility_size,
            "portfolio_used_capacity": portfolio['used_capacity']
        }

    if industry_total + facility_size > 20_000_000:
        return {
            "decision": "Declined",
            "reason": f"Industry exposure for {industry} would exceed $20MM limit",
            "facility_size": facility_size,
            "portfolio_used_capacity": portfolio['used_capacity']
        }

    if borrower_total + facility_size > 15_000_000:
        return {
            "decision": "Declined",
            "reason": f"Borrower exposure would exceed $15MM limit",
            "facility_size": facility_size,
            "portfolio_used_capacity": portfolio['used_capacity']
        }

    # Auto-approved: update portfolio
    portfolio['used_capacity'] += facility_size
    portfolio['industry_exposure'][industry] = industry_total + facility_size
    portfolio['borrower_exposure'][borrower_id] = borrower_total + facility_size

    return {
        "decision": "Approved",
        "reason": "Meets all portfolio constraints",
        "facility_size": facility_size,
        "portfolio_used_capacity": portfolio['used_capacity']
    }

def pretty_print_credit_decision(decision_output):
    print("=== Credit Approval Decision ===")
    print(f"Decision: {decision_output['decision']}")
    print(f"Reason: {decision_output['reason']}")
    print(f"Facility Size: ${decision_output['facility_size']:,.2f}")
    print(f"Portfolio Used Capacity: ${decision_output['portfolio_used_capacity']:,.2f}")
