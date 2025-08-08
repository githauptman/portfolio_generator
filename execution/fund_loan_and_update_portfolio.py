def fund_loan_and_update_portfolio(executed_loan, portfolio):
    borrower_id = executed_loan['borrower_id']
    industry = executed_loan.get('industry')  # Optional, if you want to store industry
    facility_size = executed_loan['facility_size']

    portfolio['loans'].append(executed_loan)

    return portfolio
