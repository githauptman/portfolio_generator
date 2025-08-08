import json
import os
import csv
from datetime import datetime, timedelta

from borrower_generator.borrower_profile import generate_borrower_profile
from underwriting.underwrite import underwrite_loan_profile
from credit_approval.credit_approval import credit_approval_with_portfolio
from execution.issue_term_sheet import issue_term_sheet
from execution.close_loan import close_loan
from execution.fund_loan_and_update_portfolio import fund_loan_and_update_portfolio
from utils.hist_sofr import get_sofr_on_date, get_next_available_sofr  # 🔄 Use historical SOFR per loan

# === Setup output directory ===
os.makedirs("data", exist_ok=True)

# === Initialize Portfolio ===
portfolio = {
    "max_capacity": 100_000_000,
    "used_capacity": 0,
    "industry_exposure": {},
    "borrower_exposure": {},
    "loans": []
}

# === File paths ===
opportunity_log_path = "data/all_opportunities.jsonl"
portfolio_snapshot_path = "data/final_portfolio.json"
opportunities_csv_path = "data/opportunities.csv"
funded_loans_csv_path = "data/funded_loans.csv"

# === CSV field names ===
csv_fields = [
    "borrower_id", "decision", "reason", "facility_size", "loan_type",
    "pd", "lgd", "term_years", "spread_bps", "total_rate", "funding_date"
]

# === Funding calendar: simulate over 2 years ===
funding_start_date = datetime.strptime("2019-1-01", "%Y-%m-%d")
funding_interval = timedelta(days=7)  # Weekly loan funding

current_date = funding_start_date

# === CSV files (initialize headers) ===
with open(opportunities_csv_path, "w", newline="") as opp_csv, \
     open(funded_loans_csv_path, "w", newline="") as funded_csv:

    opp_writer = csv.DictWriter(opp_csv, fieldnames=csv_fields)
    funded_writer = csv.DictWriter(funded_csv, fieldnames=csv_fields)

    opp_writer.writeheader()
    funded_writer.writeheader()

    # === JSONL file for all opportunity logs ===
    with open(opportunity_log_path, "w") as opportunity_log:

        while portfolio["used_capacity"] < 0.95 * portfolio["max_capacity"]:
            funding_date_str = current_date.strftime("%Y-%m-%d")
            sofr = get_sofr_on_date(funding_date_str)
            sofr, actual_funding_date_str = get_next_available_sofr(funding_date_str)
            if sofr is None:
                current_date += funding_interval
                continue


            # Step 1: Generate borrower
            profile = generate_borrower_profile()

            # Step 2: Underwrite using historical SOFR
            underwriting_output = underwrite_loan_profile(profile, sofr)

            # Step 3: Credit Approval
            decision = credit_approval_with_portfolio(underwriting_output, portfolio)

            borrower_id = profile["borrower_id"]
            cm = underwriting_output["credit_metrics"]
            pricing = underwriting_output["pricing"]

            # Flatten record for CSV
            row = {
                "borrower_id": borrower_id,
                "decision": decision["decision"],
                "reason": decision["reason"],
                "facility_size": cm["facility_size"],
                "loan_type": cm["loan_type"],
                "pd": cm["probability_of_default"],
                "lgd": cm["loss_given_default"],
                "term_years": cm["term_years"] if isinstance(cm["term_years"], int) else json.dumps(cm["term_years"]),
                "spread_bps": pricing["spread_bps"],
                "total_rate": pricing["total_rate"],
                "funding_date": actual_funding_date_str
            }

            # Log CSV + JSONL
            opp_writer.writerow(row)
            opportunity_log.write(json.dumps({
                "borrower_id": borrower_id,
                "underwriting_output": underwriting_output,
                "decision": decision,
                "funding_date": funding_date_str
            }) + "\n")

            if decision["decision"] == "Approved":
                term_sheet = issue_term_sheet(underwriting_output)
                executed_loan = close_loan(term_sheet)
                portfolio = fund_loan_and_update_portfolio(executed_loan, portfolio)
                funded_writer.writerow(row)
                print(f"✅ Executed loan for Borrower {borrower_id} on {actual_funding_date_str}")
            else:
                print(f"❌ Declined Borrower {borrower_id} on {actual_funding_date_str}: {decision['reason']}")

            # Advance to the next funding date
            current_date += funding_interval

# === Save final portfolio state ===
with open(portfolio_snapshot_path, "w") as f:
    json.dump(portfolio, f, indent=4)

print(f"\n🏁 Portfolio reached {portfolio['used_capacity'] / portfolio['max_capacity']:.1%} capacity.")
print(f"📁 Data saved to 'data/' folder.")
