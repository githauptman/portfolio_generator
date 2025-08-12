import pandas as pd
import numpy as np
import re
from pathlib import Path

# =================== Config ===================
EFFR_PATH = Path("data/EFFR.csv")
LOANS_PATH = Path("data/loans.csv")
OUTPUT_TRANSACTIONS = Path("data/BT_Results/portfolio_transactions.csv")
OUTPUT_POSITIONS = Path("data/BT_Results/portfolio_positions.csv")
OUTPUT_PNL = Path("data/BT_Results/weekly_pnl.csv")
OUTPUT_PNL_WEEKTOTALS = Path("data/BT_Results/weekly_totals.csv")  
OUTPUT_PNL_WIDE = Path("data/BT_Results/weekly_pnl_wide.csv")      
OUTPUT_YEARLY = Path("data/BT_Results/yearly_stats.csv")           
OUTPUT_OVERALL = Path("data/BT_Results/overall_stats.csv")         
OUTPUT_DRAWDOWN = Path("data/BT_Results/drawdown_curve.csv")       

INITIAL_TARGET = 100_000_000      
YEAR_DAY_COUNT = 365              
RNG_SEED = 7                      
MAX_WEEKS_TO_PRINT = None         


WEEKS_PER_YEAR = 52               
PNL_PRINT_LIMIT = None           
# ==============================================

def normalize_cols(df: pd.DataFrame) -> pd.DataFrame:
    def norm(c):
        c = str(c).strip().lower()
        c = re.sub(r"[^a-z0-9]+", "_", c)
        c = re.sub(r"_+", "_", c).strip("_")
        return c
    out = df.copy()
    out.columns = [norm(c) for c in df.columns]
    return out

def resolve_column(candidates, df):
    for c in candidates:
        if c in df.columns:
            return c
    df_key = {col: col.replace("_", "") for col in df.columns}
    for c in candidates:
        key = c.replace("_", "")
        for col, nosym in df_key.items():
            if nosym == key:
                return col
    return None

def load_inputs(effr_path: Path, loans_path: Path):
    effr_raw = pd.read_csv(effr_path)
    loans_raw = pd.read_csv(loans_path)

    effr = normalize_cols(effr_raw)
    loans = normalize_cols(loans_raw)

    # EFFR
    date_col, rate_col = effr.columns[0], effr.columns[1]
    effr["date"] = pd.to_datetime(effr[date_col], errors="coerce")
    effr["effr_pct"] = pd.to_numeric(effr[rate_col], errors="coerce")
    effr = effr.dropna(subset=["date", "effr_pct"]).reset_index(drop=True)

    # Loans
    facility_col = resolve_column(["facility_size","facility_amount","loan_amount","facility"], loans)
    pd_col       = resolve_column(["pd","prob_default","probability_of_default"], loans)
    lgd_col      = resolve_column(["lgd","loss_given_default"], loans)
    term_col     = resolve_column(["term_years","term_loan","term","tenor","maturity_years"], loans)
    spread_col   = resolve_column(["spread_bps","spreadbps","spread","spread_bp"], loans)

    required = {
        "facility_size": facility_col,
        "pd": pd_col,
        "lgd": lgd_col,
        "term_years": term_col,
        "spread_bps": spread_col,
    }
    missing = [k for k, v in required.items() if v is None]
    if missing:
        raise ValueError(f"Missing required columns in funded_loans.csv: {missing}\n"
                         f"Available columns (normalized): {list(loans.columns)}")

    loans_small = loans[[facility_col, pd_col, lgd_col, term_col, spread_col]].copy()
    loans_small.columns = ["facility_size","pd","lgd","term_years","spread_bps"]
    for col in ["facility_size","pd","lgd","term_years","spread_bps"]:
        loans_small[col] = pd.to_numeric(loans_small[col], errors="coerce")
    loans_small = loans_small.dropna().reset_index(drop=True)
    loans_small = loans_small[loans_small["facility_size"] > 0].reset_index(drop=True)

    if loans_small.empty or effr.empty:
        raise ValueError("Input data problem: no usable EFFR rows or loans after cleaning.")

    return effr, loans_small

def random_pack_under_cap(loans_df: pd.DataFrame, cap: float, rng: np.random.Generator) -> pd.DataFrame:

    if cap <= 0:
        return loans_df.iloc[[]].copy()

    loan_mat = loans_df.values
    n_loans = loan_mat.shape[0]
    fac_idx = loans_df.columns.get_loc("facility_size")
    min_fac = float(loans_df["facility_size"].min())

    picked_rows = []
    total = 0.0
    safety = 0
    while cap - total >= min_fac and safety < 1_000_000:
        i = rng.integers(0, n_loans)
        row = loan_mat[i]
        fac = float(row[fac_idx])
        if total + fac <= cap + 1e-12:
            picked_rows.append(row)
            total += fac
        safety += 1

    return pd.DataFrame(picked_rows, columns=loans_df.columns)

def build_weekly_pnl(effr: pd.DataFrame, transactions: pd.DataFrame) -> pd.DataFrame:

    weeks = pd.to_datetime(effr["date"]).dt.date.tolist()

    tx = transactions.copy()
    tx["date"] = pd.to_datetime(tx["date"], errors="coerce").dt.date

    fund = tx[tx["type"] == "FUND"].sort_values(["loan_id","date"]).drop_duplicates("loan_id", keep="first")
    fund = fund.rename(columns={"date": "fund_date"})
    ends = tx[tx["type"].isin(["DEFAULT","MATURE"])].sort_values(["loan_id","date"])
    ends = ends.groupby("loan_id").first().reset_index().rename(columns={"date": "end_date", "type": "end_type"})

    loans = fund.merge(ends[["loan_id","end_date","end_type"]], on="loan_id", how="left")
    loans = loans[["loan_id","fund_date","facility_size","lgd","total_rate","end_date","end_type"]]

    rows = []
    for _, L in loans.iterrows():
        fund_date = L["fund_date"]
        end_date = L["end_date"] if pd.notna(L["end_date"]) else None
        end_type = L["end_type"] if isinstance(L["end_type"], str) else None
        last_week = weeks[-1] if end_date is None else end_date

        for w in weeks:
            if w < fund_date:
                continue
            if w > last_week:
                break

            exposure = float(L["facility_size"])  # full facility counts for the week
            interest = exposure * float(L["total_rate"]) / WEEKS_PER_YEAR
            default_loss = 0.0
            ended_flag = False
            etype = ""

            if end_type == "DEFAULT" and end_date is not None and w == end_date:
                default_loss = float(L["lgd"]) * exposure
                ended_flag = True
                etype = "DEFAULT"
            elif end_type == "MATURE" and end_date is not None and w == end_date:
                ended_flag = True
                etype = "MATURE"

            pnl = interest - default_loss
            rows.append({
                "week": w,
                "loan_id": int(L["loan_id"]),
                "exposure": exposure,
                "interest": interest,
                "default_loss": default_loss,
                "pnl": pnl,
                "ended_this_week": ended_flag,
                "end_type": etype
            })

    pnl_df = pd.DataFrame(rows).sort_values(["week","loan_id"]).reset_index(drop=True)
    return pnl_df

def main():
    #inputs
    effr, loans_small = load_inputs(EFFR_PATH, LOANS_PATH)
    rng = np.random.default_rng(RNG_SEED)

    #ID
    next_id = 1
    def assign_ids(df: pd.DataFrame) -> pd.DataFrame:
        nonlocal next_id
        n = len(df)
        df = df.copy()
        df["loan_id"] = range(next_id, next_id + n)
        next_id += n
        return df

    #Initial funding
    start_date = effr.loc[0, "date"].date()
    start_effr_pct = float(effr.loc[0, "effr_pct"])
    start_effr_dec = start_effr_pct / 100.0

    initial = random_pack_under_cap(loans_small, INITIAL_TARGET, rng).reset_index(drop=True)
    initial = assign_ids(initial)
    initial["date_funded"] = pd.to_datetime(start_date)
    initial["maturity_date"] = initial["date_funded"] + initial["term_years"].apply(
        lambda y: pd.to_timedelta(int(round(y * YEAR_DAY_COUNT)), unit="D")
    )
    initial["total_rate"] = start_effr_dec + (initial["spread_bps"] / 10_000.0)

    positions = initial.copy()
    transactions = []
    for _, r in positions.iterrows():
        transactions.append({
            "loan_id": int(r["loan_id"]),
            "date": r["date_funded"].date(),
            "type": "FUND",
            "facility_size": float(r["facility_size"]),
            "pd": float(r["pd"]),
            "lgd": float(r["lgd"]),
            "term_years": float(r["term_years"]),
            "spread_bps": float(r["spread_bps"]),
            "total_rate": float(r["total_rate"]),
            "recovery": 0.0,
            "loss": 0.0
        })

    cash = 0.0
    printed = 0

    def header(week_idx, week_date, effr_pct):
        print(f"\n=== Week {week_idx} | {week_date} | EFFR {effr_pct:.3f}% ===")

    #Weekly roll-forward
    for week_idx in range(1, len(effr)):
        week_date = effr.loc[week_idx, "date"].date()
        effr_pct = float(effr.loc[week_idx, "effr_pct"])
        effr_dec = effr_pct / 100.0

        need_header = True

        #Collect weekly interest
        if not positions.empty:
            weekly_interest = (positions["facility_size"] * positions["total_rate"] / WEEKS_PER_YEAR).sum()
            cash += float(weekly_interest)
            if MAX_WEEKS_TO_PRINT is None or printed < MAX_WEEKS_TO_PRINT:
                header(week_idx, week_date, effr_pct)
                need_header = False
                print(f"Collected interest this week: {weekly_interest:,.0f} -> cash now {cash:,.0f}")
                printed += 1

        #Weekly DEFAULT 
        if not positions.empty:
            pd_clip = positions["pd"].clip(lower=0.0, upper=0.999999)
            lgd_clip = positions["lgd"].clip(lower=0.0, upper=1.0)
            p_week = 1.0 - (1.0 - pd_clip) ** (1.0 / 52.0)
            draws = rng.random(len(positions))
            default_mask = draws < p_week.values

            if default_mask.any():
                defaults = positions[default_mask].copy()
                recoveries = (1.0 - lgd_clip[default_mask].values) * defaults["facility_size"].values
                losses = lgd_clip[default_mask].values * defaults["facility_size"].values
                rec_total = float(np.sum(recoveries))
                loss_total = float(np.sum(losses))

                if MAX_WEEKS_TO_PRINT is None or printed < MAX_WEEKS_TO_PRINT:
                    if need_header:
                        header(week_idx, week_date, effr_pct)
                        need_header = False
                    print(f"Defaults this week: {len(defaults)}  (recovery {rec_total:,.0f}, loss {loss_total:,.0f})")
                    for _, r in defaults.iterrows():
                        lgd_val = float(r["lgd"])
                        rec = (1.0 - lgd_val) * float(r["facility_size"])
                        loss = lgd_val * float(r["facility_size"])
                        print(f"  x DEFAULT Loan #{int(r['loan_id'])} "
                              f"facility {r['facility_size']:,.0f} | LGD {lgd_val:.2f} "
                              f"-> recovery {rec:,.0f}, loss {loss:,.0f}")
                    printed += 1

                cash += rec_total  
                for _, r in defaults.iterrows():
                    lgd_val = float(r["lgd"])
                    rec = (1.0 - lgd_val) * float(r["facility_size"])
                    loss = lgd_val * float(r["facility_size"])
                    transactions.append({
                        "loan_id": int(r["loan_id"]),
                        "date": week_date,
                        "type": "DEFAULT",
                        "facility_size": float(r["facility_size"]),
                        "pd": float(r["pd"]),
                        "lgd": lgd_val,
                        "term_years": float(r["term_years"]),
                        "spread_bps": float(r["spread_bps"]),
                        "total_rate": float(r["total_rate"]),
                        "recovery": rec,
                        "loss": loss
                    })

                positions = positions[~default_mask].reset_index(drop=True)

        #Maturities 
        matured_mask = positions["maturity_date"].dt.date <= week_date
        matured = positions[matured_mask].copy()
        if not matured.empty:
            if MAX_WEEKS_TO_PRINT is None or printed < MAX_WEEKS_TO_PRINT:
                if need_header:
                    header(week_idx, week_date, effr_pct)
                    need_header = False
                print(f"Loans matured: {len(matured)}")
                for _, r in matured.iterrows():
                    print(f"  - Loan #{int(r['loan_id'])} matured, "
                          f"facility {r['facility_size']:,.0f} (funded {r['date_funded'].date()}, "
                          f"term {r['term_years']}) -> cash in")
                printed += 1

            cash_in = float(matured["facility_size"].sum())
            cash += cash_in
            for _, r in matured.iterrows():
                transactions.append({
                    "loan_id": int(r["loan_id"]),
                    "date": week_date,
                    "type": "MATURE",
                    "facility_size": float(r["facility_size"]),
                    "pd": float(r["pd"]),
                    "lgd": float(r["lgd"]),
                    "term_years": float(r["term_years"]),
                    "spread_bps": float(r["spread_bps"]),
                    "total_rate": float(r["total_rate"]),
                    "recovery": float(r["facility_size"]),
                    "loss": 0.0
                })
            positions = positions[~matured_mask].reset_index(drop=True)

        #Reinvest cash at this week's rate
        if cash > 0:
            pack = random_pack_under_cap(loans_small, cash, np.random.default_rng(RNG_SEED + 10 + week_idx)).reset_index(drop=True)
            if not pack.empty:
                pack = assign_ids(pack)
                pack["date_funded"] = pd.to_datetime(week_date)
                pack["maturity_date"] = pack["date_funded"] + pack["term_years"].apply(
                    lambda y: pd.to_timedelta(int(round(y * YEAR_DAY_COUNT)), unit="D")
                )
                pack["total_rate"] = effr_dec + (pack["spread_bps"] / 10_000.0)

                spent = float(pack["facility_size"].sum())
                cash -= spent
                positions = pd.concat([positions, pack], ignore_index=True)

                if MAX_WEEKS_TO_PRINT is None or printed < MAX_WEEKS_TO_PRINT:
                    if need_header:
                        header(week_idx, week_date, effr_pct)
                    print(f"Reinvested into {len(pack)} loans, spending {spent:,.0f}. "
                          f"Remaining cash: {cash:,.0f}")
                    for _, r in pack.iterrows():
                        print(f"  + Funded Loan #{int(r['loan_id'])}, facility {r['facility_size']:,.0f} "
                              f"at total_rate {r['total_rate']:.4f}")
                    printed += 1

                for _, r in pack.iterrows():
                    transactions.append({
                        "loan_id": int(r["loan_id"]),
                        "date": week_date,
                        "type": "FUND",
                        "facility_size": float(r["facility_size"]),
                        "pd": float(r["pd"]),
                        "lgd": float(r["lgd"]),
                        "term_years": float(r["term_years"]),
                        "spread_bps": float(r["spread_bps"]),
                        "total_rate": float(r["total_rate"]),
                        "recovery": 0.0,
                        "loss": 0.0
                    })
            else:
                if MAX_WEEKS_TO_PRINT is None or printed < MAX_WEEKS_TO_PRINT:
                    if need_header:
                        header(week_idx, week_date, effr_pct)
                    print(f"Cash {cash:,.0f} too small to fund any loan this week.")
                    printed += 1

    # Save positions & transactions
    positions_out = positions.copy()
    positions_out["date_funded"] = positions_out["date_funded"].dt.date
    positions_out["maturity_date"] = positions_out["maturity_date"].dt.date
    positions_out = positions_out[
        ["loan_id","date_funded","maturity_date","facility_size","pd","lgd","term_years","spread_bps","total_rate"]
    ]
    positions_out.to_csv(OUTPUT_POSITIONS, index=False)

    tx = pd.DataFrame(transactions)
    tx = tx[["loan_id","date","type","facility_size","pd","lgd","term_years","spread_bps","total_rate","recovery","loss"]]
    tx.to_csv(OUTPUT_TRANSACTIONS, index=False)

    print("\n--- Simulation complete ---")
    print(f"Outstanding positions: {len(positions_out)}")
    print(f"Total outstanding facility: {positions_out['facility_size'].sum():,.0f}")
    print(f"Transactions saved to: {OUTPUT_TRANSACTIONS}")
    print(f"Positions saved to: {OUTPUT_POSITIONS}")

    # Build & save weekly P&L
    weekly_pnl = build_weekly_pnl(effr, tx)
    weekly_pnl.to_csv(OUTPUT_PNL, index=False)

    # Weekly totals
    wk = weekly_pnl.groupby("week", as_index=False).agg(
        interest=("interest","sum"),
        default_loss=("default_loss","sum"),
        pnl=("pnl","sum"),
        exposure=("exposure","sum")
    )
    wk = wk.sort_values("week").reset_index(drop=True)
    wk["cum_pnl"] = wk["pnl"].cumsum()
    wk["roll_max"] = wk["cum_pnl"].cummax()
    wk["drawdown_amt"] = (wk["roll_max"] - wk["cum_pnl"]).clip(lower=0)
    wk["drawdown_pct"] = np.where(wk["roll_max"] > 0, wk["drawdown_amt"] / wk["roll_max"], np.nan)
    wk.to_csv(OUTPUT_PNL_WEEKTOTALS, index=False)
    wk[["week","cum_pnl","roll_max","drawdown_amt","drawdown_pct"]].to_csv(OUTPUT_DRAWDOWN, index=False)

    max_dd_amt = wk["drawdown_amt"].max()
    dd_idx = wk["drawdown_amt"].idxmax()
    max_dd_pct = float(wk.loc[dd_idx, "drawdown_pct"]) if pd.notna(dd_idx) else np.nan

    #Weekly total P&L
    totals_rows = wk[["week","pnl"]].rename(columns={"pnl":"total_pnl"})
    totals_rows.to_csv(OUTPUT_PNL_WIDE, index=False)

    #Yearly stats
    wk["year"] = pd.to_datetime(wk["week"]).dt.year
    yearly_core = wk.groupby("year", as_index=False).agg(
        total_interest=("interest","sum"),
        total_default_loss=("default_loss","sum"),
        total_pnl=("pnl","sum"),
        avg_exposure=("exposure","mean"),
        weeks=("week","count"),
        weekly_volatility_pnl=("pnl","std")
    )
    yearly_core["return_pct"] = np.where(yearly_core["avg_exposure"] > 0,
                                         yearly_core["total_pnl"] / yearly_core["avg_exposure"],
                                         np.nan)

    tx2 = tx.copy()
    tx2["year"] = pd.to_datetime(tx2["date"]).dt.year

    funds = tx2[tx2["type"]=="FUND"].copy()
    funds_by_year = funds.groupby("year").agg(
        loans_funded=("loan_id","count"),
        funded_amount=("facility_size","sum"),
        wa_total_rate=("total_rate", lambda s: np.average(s, weights=funds.loc[s.index,"facility_size"]) if s.size>0 else np.nan),
        wa_spread_bps=("spread_bps", lambda s: np.average(s, weights=funds.loc[s.index,"facility_size"]) if s.size>0 else np.nan),
        wa_pd=("pd", lambda s: np.average(s, weights=funds.loc[s.index,"facility_size"]) if s.size>0 else np.nan),
        wa_term_years=("term_years", lambda s: np.average(s, weights=funds.loc[s.index,"facility_size"]) if s.size>0 else np.nan)
    ).reset_index()

    defs = tx2[tx2["type"]=="DEFAULT"].groupby("year", as_index=False).agg(
        loans_defaulted=("loan_id","count"),
        avg_lgd_on_defaults=("lgd","mean"),
        defaulted_amount=("facility_size","sum")
    )

    yearly = yearly_core.merge(funds_by_year, on="year", how="left").merge(defs, on="year", how="left")
    for col in ["loans_funded","funded_amount","wa_total_rate","wa_spread_bps","wa_pd","wa_term_years",
                "loans_defaulted","avg_lgd_on_defaults","defaulted_amount"]:
        if col not in yearly:
            yearly[col] = np.nan
    yearly["default_rate_by_count"] = yearly["loans_defaulted"] / yearly["loans_funded"]
    yearly.to_csv(OUTPUT_YEARLY, index=False)

    #Overall stats
    overall = pd.DataFrame([{
        "total_interest": wk["interest"].sum(),
        "total_default_loss": wk["default_loss"].sum(),
        "total_pnl": wk["pnl"].sum(),
        "avg_weekly_exposure": wk["exposure"].mean(),
        "overall_return_pct": (wk["pnl"].sum() / wk["exposure"].mean()) if wk["exposure"].mean() > 0 else np.nan,
        "weeks": len(wk),
        "loans_funded_total": int((tx2["type"]=="FUND").sum()),
        "loans_defaulted_total": int((tx2["type"]=="DEFAULT").sum()),
        "funded_amount_total": float(tx2.loc[tx2["type"]=="FUND","facility_size"].sum()),
        "defaulted_amount_total": float(tx2.loc[tx2["type"]=="DEFAULT","facility_size"].sum()),
        "max_drawdown_amt": float(max_dd_amt),
        "max_drawdown_pct": float(max_dd_pct) if pd.notna(max_dd_pct) else np.nan
    }])
    overall.to_csv(OUTPUT_OVERALL, index=False)

    print("\n--- Portfolio Stats ---")
    print(f"Overall P&L: {overall.at[0,'total_pnl']:,.0f} | Overall return: {overall.at[0,'overall_return_pct']:.2%} "
          f"| Max DD: {overall.at[0,'max_drawdown_amt']:,.0f} ({overall.at[0,'max_drawdown_pct']:.2%})")
    print(f"Total loans funded: {overall.at[0,'loans_funded_total']} | defaults: {overall.at[0,'loans_defaulted_total']}")
    print(f"Yearly stats written to: {OUTPUT_YEARLY}")
    print(f"Overall stats written to: {OUTPUT_OVERALL}")
    print(f"Drawdown curve written to: {OUTPUT_DRAWDOWN}")

if __name__ == "__main__":
    main()
