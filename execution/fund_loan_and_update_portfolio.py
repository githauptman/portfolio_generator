def fund_loan_and_update_portfolio(executed_loan, portfolio, underwriting_output):
    """
    Funds a loan and updates the portfolio with all relevant data.

    Args:
        executed_loan (dict): Executed loan details.
        portfolio (dict): Current portfolio state.
        underwriting_output (dict): Full underwriting output including borrower profile and pricing.

    Returns:
        dict: Updated portfolio.
    """
    borrower_id = underwriting_output['borrower_profile']['borrower_id']
    industry = underwriting_output['borrower_profile']['industry']['industry']
    facility_size = underwriting_output['credit_metrics']['facility_size']

    # Update capacity and exposures
    portfolio['used_capacity'] += facility_size
    portfolio['industry_exposure'][industry] = portfolio['industry_exposure'].get(industry, 0) + facility_size
    portfolio['borrower_exposure'][borrower_id] = portfolio['borrower_exposure'].get(borrower_id, 0) + facility_size

    # Record full loan object with underwriting + profile
    loan_record = {
        "borrower_id": borrower_id,
        "executed_loan": executed_loan,
        "underwriting_output": underwriting_output,
        "borrower_profile": underwriting_output['borrower_profile']
    }

    portfolio['loans'].append(loan_record)

    return portfolio
