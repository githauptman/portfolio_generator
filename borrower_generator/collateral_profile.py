import random

def generate_collateral_profile():
    """
    Randomly selects a collateral quality (weighted) and generates a collateral profile.
    Returns asset type, aging, concentration, lien validity, and audit status.
    """

    # Weighted random selection: 50% high, 30% medium, 20% low
    collateral_quality = random.choices(
        population=["high", "medium", "low"],
        weights=[0.5, 0.3, 0.2],
        k=1
    )[0]

    if collateral_quality == "high":
        asset_type = random.choice(["accounts receivable", "inventory", "equipment"])
        aging = random.randint(20, 45)  # days
        concentration = round(random.uniform(5, 15), 1)  # % top 1-2 customers
        lien_valid = True
        audit_status = "clean"

    elif collateral_quality == "medium":
        asset_type = random.choice(["inventory", "equipment", "mixed A/R & inventory"])
        aging = random.randint(45, 75)
        concentration = round(random.uniform(15, 30), 1)
        lien_valid = random.choice([True, True, False])
        audit_status = random.choice(["clean", "minor issues"])

    else:  # low
        asset_type = random.choice(["work-in-progress", "aged receivables", "misc. inventory"])
        aging = random.randint(75, 120)
        concentration = round(random.uniform(30, 60), 1)
        lien_valid = random.choice([True, False])
        audit_status = random.choice(["issues", "pending", "unknown"])

    return {
        "collateral_quality": collateral_quality,
        "asset_type": asset_type,
        "average_aging_days": aging,
        "concentration_pct": concentration,
        "lien_valid": lien_valid,
        "audit_status": audit_status
    }
