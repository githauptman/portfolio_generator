def recommend_loan_term(borrower_profile, loan_type):
    """
    Recommends loan term in years based on borrower's credit profile and loan type.

    Args:
        borrower_profile (dict): The full borrower profile including 'financial', 'collateral', etc.
        loan_type (str): "Revolver", "Term Loan", or "Hybrid"

    Returns:
        dict or int: Recommended term in years. Returns a dict if Hybrid.
    """
    credit_strength = borrower_profile['financial']['credit_strength']

    # Normalize credit tier
    if credit_strength == "strong":
        tier = "strong"
    elif credit_strength == "moderate":
        tier = "medium"
    else:
        tier = "weak"

    # Define mappings
    revolver_terms = {
        "strong": 5,
        "medium": 4,
        "weak": 3
    }

    term_loan_terms = {
        "strong": 5,
        "medium": 4,
        "weak": 3
    }

    # Logic for different loan types
    if loan_type == "Revolver":
        return revolver_terms[tier]

    elif loan_type == "Term Loan":
        return term_loan_terms[tier]

    elif loan_type == "Hybrid (Term + Revolver)":
        return {
            "Revolver": revolver_terms[tier],
            "Term Loan": term_loan_terms[tier]
        }

    else:
        raise ValueError("Invalid loan_type. Must be 'Revolver', 'Term Loan', or 'Hybrid (Term + Revolver)'.")
