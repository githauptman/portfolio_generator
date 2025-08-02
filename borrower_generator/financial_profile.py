import random

def generate_financial_profile():
    """
    Randomly selects a credit quality (weighted) and returns a financial profile.
    """
    credit_quality = random.choices(
        population=["strong", "medium", "weak"],
        weights=[0.2, 0.6, 0.2],  # 60% chance for 'medium', 20% each for others
        k=1
    )[0]

    if credit_quality == "strong":
        revenue = random.randint(75, 120) * 1_000_000
        ebitda_margin = round(random.uniform(15, 25), 1)
        leverage = round(random.uniform(1.5, 2.5), 1)
        fccr = round(random.uniform(2.5, 3.5), 1)
        liquidity = round(random.uniform(5, 10), 1)
        credit_strength = "strong"

    elif credit_quality == "medium":
        revenue = random.randint(30, 60) * 1_000_000
        ebitda_margin = round(random.uniform(10, 15), 1)
        leverage = round(random.uniform(2.5, 3.5), 1)
        fccr = round(random.uniform(1.5, 2.5), 1)
        liquidity = round(random.uniform(2, 5), 1)
        credit_strength = "moderate"

    else:  # weak
        revenue = random.randint(15, 30) * 1_000_000
        ebitda_margin = round(random.uniform(6, 10), 1)
        leverage = round(random.uniform(3.5, 5.0), 1)
        fccr = round(random.uniform(1.0, 1.5), 1)
        liquidity = round(random.uniform(0.5, 2.0), 1)
        credit_strength = "weak"

    return {
        "credit_strength": credit_strength,
        "revenue": revenue,
        "ebitda_margin": ebitda_margin,
        "leverage": leverage,
        "fccr": fccr,
        "liquidity": liquidity
    }
