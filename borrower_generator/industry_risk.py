import random

def generate_industry_and_business_risk():
    """
    Simulate the industry and business risk profile of a borrower.
    Includes cyclicality, competitive dynamics, customer concentration, and margins.
    """

    industries = [
        "Industrial Manufacturing", "Construction Services", "Specialty Chemicals",
        "Oilfield Services", "Consumer Products", "Logistics", "Food Processing",
        "Medical Devices", "Aerospace Supply", "Packaging"
    ]

    industry = random.choice(industries)
    
    cyclicality = random.choice(["high", "moderate", "low"])
    competitive_landscape = random.choice(["fragmented", "moderately consolidated", "consolidated"])
    customer_concentration = random.choice(["diversified", "moderate", "high concentration"])
    
    ebitda_margin = round(random.uniform(5, 25), 1)  # proxy for operating leverage and pricing power
    
    # Qualitative risk summary logic
    if cyclicality == "high" or customer_concentration == "high concentration" or ebitda_margin < 10:
        overall_risk = "elevated"
    elif cyclicality == "low" and customer_concentration == "diversified" and ebitda_margin >= 15:
        overall_risk = "low"
    else:
        overall_risk = "moderate"

    return {
        "industry": industry,
        "cyclicality": cyclicality,
        "competitive_landscape": competitive_landscape,
        "customer_concentration": customer_concentration,
        "ebitda_margin_pct": ebitda_margin,
        "overall_industry_risk": overall_risk
    }
