import uuid
from .financial_profile import generate_financial_profile
from .collateral_profile import generate_collateral_profile
from .mgmt_profile import generate_management_and_sponsor_profile
from .industry_risk import generate_industry_and_business_risk

def generate_borrower_profile():
    borrower_id = str(uuid.uuid4())  # Unique borrower identifier

    return {
        "borrower_id": borrower_id,
        "financial": generate_financial_profile(),
        "collateral": generate_collateral_profile(),
        "management": generate_management_and_sponsor_profile(),
        "industry": generate_industry_and_business_risk()
    }

# Print Function
def print_borrower_profile(profile):
    print("\n=== Borrower Profile Summary ===")

    for section_name, section_data in profile.items():
        print(f"\n-- {section_name.capitalize()} Profile --")
        for key, value in section_data.items():
            label = key.replace('_', ' ').capitalize()
            if isinstance(value, float):
                print(f"{label}: {value:.2f}")
            elif isinstance(value, int):
                print(f"{label}: ${value:,.0f}" if 'revenue' in key or 'liquidity' in key else f"{label}: {value}")
            else:
                print(f"{label}: {value}")
