def issue_term_sheet(underwriting_output):
    return {
        "borrower_id": underwriting_output['borrower_profile']['borrower_id'],
        "loan_type": underwriting_output['credit_metrics']['loan_type'],
        "facility_size": underwriting_output['credit_metrics']['facility_size'],
        "term_years": underwriting_output['credit_metrics']['term_years'],
        "spread_bps": underwriting_output['pricing']['spread_bps'],
        "origination_fee_pct": underwriting_output['pricing']['origination_fee_pct'],
        "unused_fee_pct": underwriting_output['pricing']['unused_fee_pct'],
        "total_rate": underwriting_output['pricing']['total_rate']
    }
