def close_loan(term_sheet):
    #print(f"Loan for borrower {term_sheet['borrower_id']} successfully closed.")
    return {
        "borrower_id": term_sheet['borrower_id'],
        "loan_type": term_sheet['loan_type'],
        "facility_size": term_sheet['facility_size'],
        "interest_rate": term_sheet['total_rate'],
        "term_years": term_sheet['term_years'],
        "status": "Funded"
    }
