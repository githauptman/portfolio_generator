import random

def generate_management_and_sponsor_profile():
    """
    Simulate the management and sponsor profile for a borrower.
    Returns attributes like experience, track record, sponsor strength, and alignment.
    """
    # Management team profile
    management_experience_years = random.randint(5, 30)
    management_stability = random.choice(["stable", "some turnover", "high turnover"])
    track_record_quality = random.choice(["strong", "moderate", "limited"])

    # Sponsor profile
    sponsor_type = random.choice(["independent", "family office", "private equity"])
    sponsor_reputation = random.choice(["excellent", "good", "average", "unknown"])
    sponsor_equity_contribution = round(random.uniform(5, 25), 1)  # in percent of total capitalization
    alignment = "high" if sponsor_equity_contribution > 15 else "moderate" if sponsor_equity_contribution > 10 else "low"

    # Derive sponsor_strength based on sponsor_reputation and alignment
    if sponsor_reputation in ["excellent", "good"] and alignment == "high":
        sponsor_strength = "strong"
    elif sponsor_reputation == "average" or alignment == "moderate":
        sponsor_strength = "moderate"
    else:
        sponsor_strength = "weak"

    return {
        "management_experience_years": management_experience_years,
        "management_stability": management_stability,
        "track_record_quality": track_record_quality,
        "sponsor_type": sponsor_type,
        "sponsor_reputation": sponsor_reputation,
        "sponsor_equity_contribution_pct": sponsor_equity_contribution,
        "alignment": alignment,
        "sponsor_strength": sponsor_strength  # <== Added key here
    }
