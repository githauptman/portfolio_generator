File Structure:
.
├── borrower_generator/
│   ├── __init__.py
│   ├── financial_profile.py
│   ├── collateral_profile.py
│   ├── mgmt_profile.py
│   ├── industry_risk.py
│   └── borrower_profile.py         # combines all above into a borrower dict

├── underwriting/
│   ├── __init__.py
│   ├── structure_and_pricing.py    # generates structured loan terms
│   ├── facility_size.py
│   ├── credit_risk.py              # PD, LGD, expected loss logic
│   └── term_generator.py           # assigns term length, revolver vs term

├── approval/
│   ├── __init__.py
│   └── credit_approval.py          # auto-approval logic, capacity checks

├── execution/
│   ├── __init__.py
│   ├── term_sheet_generator.py     # outlines final terms
│   ├── funding.py                  # "funds" deal & adds to portfolio
│   └── portfolio_tracker.py        # tracks current capacity and holdings

├── data/
│   ├── portfolio_snapshot.csv
│   ├── all_loan_opportunities.csv

├── utils/
│   ├── __init__.py
│   ├── logger.py
│   └── sofr.py

├── main.py                         # orchestrates full deal lifecycle

