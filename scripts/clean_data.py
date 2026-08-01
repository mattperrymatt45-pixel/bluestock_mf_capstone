"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 2: Data Cleaning

Cleans and validates all 10 raw datasets and writes the results to
data/processed/. Detailed, task-specific cleaning logic is implemented for:

  Task 1 - 02_nav_history.csv         (clean_nav_history)
  Task 2 - 08_investor_transactions.csv (clean_investor_transactions)
  Task 3 - 07_scheme_performance.csv  (clean_scheme_performance)

The remaining 7 datasets go through a shared baseline cleaning routine
(date parsing, whitespace trimming, dedup, dtype checks) since the project
brief only requires deep cleaning for the three above, but all 10 processed
CSVs are needed downstream for the SQLite load (Task 5).

Usage:
    python scripts/clean_data.py
"""

from pathlib import Path
import sys
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

log_lines: list[str] = []


def log(msg: str) -> None:
    print(msg)
    log_lines.append(msg)


# ---------------------------------------------------------------------------
# Task 1: 02_nav_history.csv
# ---------------------------------------------------------------------------
def clean_nav_history() -> pd.DataFrame:
    log(f"\n{'=' * 70}\nTask 1: Cleaning 02_nav_history.csv\n{'=' * 70}")
    df = pd.read_csv(RAW_DIR / "02_nav_history.csv")
    raw_rows = len(df)

    # Parse dates to datetime
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
    bad_dates = df["date"].isnull().sum()
    if bad_dates:
        log(f"  Dropping {bad_dates} row(s) with unparseable dates.")
        df = df.dropna(subset=["date"])

    # Sort by amfi_code + date (required before any forward-fill / rolling calc)
    df = df.sort_values(["amfi_code", "date"]).reset_index(drop=True)

    # Remove duplicates (exact dupes, and dupes on the natural key amfi_code+date)
    exact_dupes = df.duplicated().sum()
    key_dupes = df.duplicated(subset=["amfi_code", "date"]).sum()
    df = df.drop_duplicates()
    df = df.drop_duplicates(subset=["amfi_code", "date"], keep="last")
    log(f"  Removed {exact_dupes} exact duplicate row(s), {key_dupes} amfi_code+date duplicate(s).")

    # Validate NAV > 0
    invalid_nav = (df["nav"] <= 0) | (df["nav"].isnull())
    if invalid_nav.any():
        log(f"  Found {invalid_nav.sum()} invalid NAV (<=0 or null) row(s) - dropping.")
        df = df[~invalid_nav]

    # Forward-fill missing NAV for holidays/weekends: reindex each scheme to a
    # full business-day calendar spanning its min/max date, then ffill.
    filled_frames = []
    total_filled = 0
    for code, grp in df.groupby("amfi_code"):
        grp = grp.set_index("date").sort_index()
        full_range = pd.bdate_range(grp.index.min(), grp.index.max())
        reindexed = grp.reindex(full_range)
        n_missing = reindexed["nav"].isnull().sum()
        total_filled += n_missing
        reindexed["nav"] = reindexed["nav"].ffill()
        reindexed["amfi_code"] = code
        reindexed.index.name = "date"
        filled_frames.append(reindexed.reset_index())

    df = pd.concat(filled_frames, ignore_index=True)
    log(f"  Forward-filled {total_filled} missing business-day NAV value(s) "
        f"(0 expected for this dataset - it already covers every business day).")

    # Compute daily return (useful downstream, cheap to add here)
    df = df.sort_values(["amfi_code", "date"])
    df["daily_return_pct"] = df.groupby("amfi_code")["nav"].pct_change() * 100

    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    df = df[["amfi_code", "date", "nav", "daily_return_pct"]]

    log(f"  Rows: {raw_rows:,} raw -> {len(df):,} cleaned.")
    return df


# ---------------------------------------------------------------------------
# Task 2: 08_investor_transactions.csv
# ---------------------------------------------------------------------------
VALID_TRANSACTION_TYPES = {"SIP", "Lumpsum", "Redemption"}
VALID_KYC_STATUS = {"Verified", "Pending"}


def clean_investor_transactions() -> pd.DataFrame:
    log(f"\n{'=' * 70}\nTask 2: Cleaning 08_investor_transactions.csv\n{'=' * 70}")
    df = pd.read_csv(RAW_DIR / "08_investor_transactions.csv")
    raw_rows = len(df)

    # Standardise transaction_type: trim whitespace, normalise case to the
    # canonical values (SIP / Lumpsum / Redemption)
    canonical_map = {v.lower(): v for v in VALID_TRANSACTION_TYPES}
    df["transaction_type"] = df["transaction_type"].str.strip()
    normalised = df["transaction_type"].str.lower().map(canonical_map)
    unmapped = normalised.isnull().sum()
    if unmapped:
        log(f"  WARNING: {unmapped} row(s) had unrecognised transaction_type "
            f"values: {df.loc[normalised.isnull(), 'transaction_type'].unique().tolist()}")
        df = df[normalised.notnull()]
        normalised = normalised.dropna()
    df["transaction_type"] = normalised
    log(f"  transaction_type standardised. Distribution:\n{df['transaction_type'].value_counts().to_string()}")

    # Fix date formats -> ISO datetime
    df["transaction_date"] = pd.to_datetime(df["transaction_date"], errors="coerce")
    bad_dates = df["transaction_date"].isnull().sum()
    if bad_dates:
        log(f"  Dropping {bad_dates} row(s) with unparseable transaction_date.")
        df = df.dropna(subset=["transaction_date"])

    # Validate amount > 0
    invalid_amount = df["amount_inr"] <= 0
    if invalid_amount.any():
        log(f"  Found {invalid_amount.sum()} row(s) with amount_inr <= 0 - dropping.")
        df = df[~invalid_amount]

    # Check KYC status enum values
    bad_kyc = ~df["kyc_status"].isin(VALID_KYC_STATUS)
    if bad_kyc.any():
        log(f"  Found {bad_kyc.sum()} row(s) with invalid kyc_status values "
            f"{df.loc[bad_kyc, 'kyc_status'].unique().tolist()} - dropping.")
        df = df[~bad_kyc]
    else:
        log(f"  kyc_status enum check passed: only {sorted(VALID_KYC_STATUS)} present.")

    # Remove exact duplicate transaction rows
    dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    log(f"  Removed {dupes} exact duplicate row(s).")

    df["transaction_date"] = df["transaction_date"].dt.strftime("%Y-%m-%d")
    log(f"  Rows: {raw_rows:,} raw -> {len(df):,} cleaned.")
    return df


# ---------------------------------------------------------------------------
# Task 3: 07_scheme_performance.csv
# ---------------------------------------------------------------------------
NUMERIC_RETURN_COLS = [
    "return_1yr_pct", "return_3yr_pct", "return_5yr_pct", "benchmark_3yr_pct",
    "alpha", "beta", "sharpe_ratio", "sortino_ratio", "std_dev_ann_pct",
    "max_drawdown_pct",
]
EXPENSE_RATIO_MIN, EXPENSE_RATIO_MAX = 0.1, 2.5


def clean_scheme_performance() -> pd.DataFrame:
    log(f"\n{'=' * 70}\nTask 3: Cleaning 07_scheme_performance.csv\n{'=' * 70}")
    df = pd.read_csv(RAW_DIR / "07_scheme_performance.csv")
    raw_rows = len(df)

    # Validate return/risk columns are numeric (coerce, flag anything that fails)
    for col in NUMERIC_RETURN_COLS:
        before_null = df[col].isnull().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after_null = df[col].isnull().sum()
        newly_bad = after_null - before_null
        if newly_bad:
            log(f"  WARNING: {col} had {newly_bad} non-numeric value(s), coerced to NaN.")

    dropped_non_numeric = df[NUMERIC_RETURN_COLS].isnull().any(axis=1).sum()
    if dropped_non_numeric:
        log(f"  Dropping {dropped_non_numeric} row(s) with non-numeric metric(s).")
        df = df.dropna(subset=NUMERIC_RETURN_COLS)
    else:
        log("  All return/risk columns are numeric - no coercion needed.")

    # Flag anomalies: negative Sharpe ratio (unusual but not necessarily invalid)
    negative_sharpe = df["sharpe_ratio"] < 0
    log(f"  Flagged {negative_sharpe.sum()} scheme(s) with negative Sharpe ratio "
        f"(kept - negative Sharpe is a valid, if poor, outcome).")
    df["flag_negative_sharpe"] = negative_sharpe

    # Check expense_ratio range (0.1% - 2.5%)
    out_of_range = (df["expense_ratio_pct"] < EXPENSE_RATIO_MIN) | (df["expense_ratio_pct"] > EXPENSE_RATIO_MAX)
    if out_of_range.any():
        log(f"  Found {out_of_range.sum()} scheme(s) with expense_ratio_pct outside "
            f"[{EXPENSE_RATIO_MIN}, {EXPENSE_RATIO_MAX}]% - flagging, not dropping.")
    else:
        log(f"  All expense_ratio_pct values fall within [{EXPENSE_RATIO_MIN}, {EXPENSE_RATIO_MAX}]%.")
    df["flag_expense_ratio_out_of_range"] = out_of_range

    dupes = df.duplicated(subset=["amfi_code"]).sum()
    df = df.drop_duplicates(subset=["amfi_code"], keep="last")
    log(f"  Removed {dupes} duplicate amfi_code row(s).")

    log(f"  Rows: {raw_rows:,} raw -> {len(df):,} cleaned.")
    return df


# ---------------------------------------------------------------------------
# Baseline cleaning for the remaining 7 datasets
# ---------------------------------------------------------------------------
DATE_COLUMNS = {
    "01_fund_master.csv": ["launch_date"],
    "03_aum_by_fund_house.csv": ["date"],
    "04_monthly_sip_inflows.csv": [],  # 'month' kept as YYYY-MM string, not a full date
    "05_category_inflows.csv": [],
    "06_industry_folio_count.csv": [],
    "09_portfolio_holdings.csv": ["portfolio_date"],
    "10_benchmark_indices.csv": ["date"],
}


def clean_baseline(filename: str) -> pd.DataFrame:
    log(f"\n{'=' * 70}\nCleaning {filename} (baseline)\n{'=' * 70}")
    df = pd.read_csv(RAW_DIR / filename)
    raw_rows = len(df)

    # Trim whitespace on all string/object columns
    str_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in str_cols:
        df[col] = df[col].str.strip()

    # Parse any known date columns
    for col in DATE_COLUMNS.get(filename, []):
        df[col] = pd.to_datetime(df[col], errors="coerce")
        bad = df[col].isnull().sum()
        if bad:
            log(f"  WARNING: {bad} unparseable value(s) in {col}.")
        df[col] = df[col].dt.strftime("%Y-%m-%d")

    # Drop exact duplicate rows
    dupes = df.duplicated().sum()
    df = df.drop_duplicates()
    log(f"  Removed {dupes} exact duplicate row(s).")

    # Null check
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls):
        log(f"  Remaining nulls:\n{nulls.to_string()}")
    else:
        log("  No nulls remaining.")

    log(f"  Rows: {raw_rows:,} raw -> {len(df):,} cleaned.")
    return df


def main() -> None:
    log("BLUESTOCK FINTECH - Day 2: Data Cleaning")

    outputs = {
        "02_nav_history.csv": clean_nav_history(),
        "08_investor_transactions.csv": clean_investor_transactions(),
        "07_scheme_performance.csv": clean_scheme_performance(),
    }

    for filename in [
        "01_fund_master.csv",
        "03_aum_by_fund_house.csv",
        "04_monthly_sip_inflows.csv",
        "05_category_inflows.csv",
        "06_industry_folio_count.csv",
        "09_portfolio_holdings.csv",
        "10_benchmark_indices.csv",
    ]:
        outputs[filename] = clean_baseline(filename)

    log(f"\n{'=' * 70}\nWriting cleaned CSVs to {PROCESSED_DIR}\n{'=' * 70}")
    for filename, df in outputs.items():
        out_name = "clean_" + filename.split("_", 1)[1] if filename[0].isdigit() else filename
        # Keep numbered prefix for traceability but also drop leading index
        out_path = PROCESSED_DIR / f"clean_{filename}"
        df.to_csv(out_path, index=False)
        log(f"  {out_path.name}: {len(df):,} rows")

    report_path = REPORTS_DIR / "cleaning_log.txt"
    with open(report_path, "w") as f:
        f.write("\n".join(log_lines))
    log(f"\nCleaning log written to: {report_path}")
    log("\nDay 2 cleaning complete. 10/10 datasets processed.")


if __name__ == "__main__":
    main()
