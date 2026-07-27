"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 1: Data Ingestion

Loads all 10 provided AMFI-sourced CSV datasets, prints shape/dtypes/head
for each, and writes a data quality / AMFI-code validation report.

Usage:
    python scripts/data_ingestion.py
"""

from pathlib import Path
import sys
import pandas as pd

# ---------------------------------------------------------------------------
# Paths (project-root relative, cross-platform via pathlib)
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

DATASETS = [
    "01_fund_master.csv",
    "02_nav_history.csv",
    "03_aum_by_fund_house.csv",
    "04_monthly_sip_inflows.csv",
    "05_category_inflows.csv",
    "06_industry_folio_count.csv",
    "07_scheme_performance.csv",
    "08_investor_transactions.csv",
    "09_portfolio_holdings.csv",
    "10_benchmark_indices.csv",
]


def load_dataset(filename: str) -> pd.DataFrame:
    """Load a single CSV from data/raw and return it as a DataFrame."""
    path = RAW_DIR / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Expected dataset not found: {path}\n"
            f"Make sure all 10 CSVs are present in data/raw/."
        )
    return pd.read_csv(path)


def inspect(name: str, df: pd.DataFrame) -> dict:
    """Print shape/dtypes/head for a dataframe and return a summary dict."""
    print(f"\n{'=' * 70}")
    print(f"{name}")
    print(f"{'=' * 70}")
    print(f"Shape        : {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"\nDtypes:\n{df.dtypes}")
    print(f"\nHead:\n{df.head(3)}")

    null_counts = df.isnull().sum()
    null_cols = null_counts[null_counts > 0]
    dup_rows = df.duplicated().sum()

    if len(null_cols):
        print(f"\nColumns with nulls:\n{null_cols}")
    else:
        print("\nNo null values.")
    print(f"Duplicate rows: {dup_rows}")

    return {
        "dataset": name,
        "rows": df.shape[0],
        "columns": df.shape[1],
        "null_cells": int(null_counts.sum()),
        "duplicate_rows": int(dup_rows),
    }


def validate_amfi_codes(fund_master: pd.DataFrame, nav_history: pd.DataFrame) -> list[str]:
    """Cross-check that every AMFI code in fund_master appears in nav_history
    and vice versa. Returns a list of findings (strings) for the quality report."""
    findings = []

    master_codes = set(fund_master["amfi_code"].astype(str))
    nav_codes = set(nav_history["amfi_code"].astype(str))

    missing_from_nav = master_codes - nav_codes
    orphaned_in_nav = nav_codes - master_codes

    findings.append(f"Unique AMFI codes in fund_master: {len(master_codes)}")
    findings.append(f"Unique AMFI codes in nav_history : {len(nav_codes)}")

    if missing_from_nav:
        findings.append(
            f"FAIL: {len(missing_from_nav)} fund_master code(s) have NO nav_history rows: "
            f"{sorted(missing_from_nav)}"
        )
    else:
        findings.append("PASS: every fund_master AMFI code has NAV history.")

    if orphaned_in_nav:
        findings.append(
            f"FAIL: {len(orphaned_in_nav)} nav_history code(s) are NOT in fund_master: "
            f"{sorted(orphaned_in_nav)}"
        )
    else:
        findings.append("PASS: every nav_history AMFI code exists in fund_master.")

    # Row count sanity check per scheme
    rows_per_scheme = nav_history.groupby("amfi_code").size()
    findings.append(
        f"NAV rows per scheme -> min: {rows_per_scheme.min()}, "
        f"max: {rows_per_scheme.max()}, mean: {rows_per_scheme.mean():.1f}"
    )
    uneven = rows_per_scheme[rows_per_scheme != rows_per_scheme.median()]
    if len(uneven):
        findings.append(
            f"NOTE: {len(uneven)} scheme(s) have a different NAV row count than the "
            f"median ({rows_per_scheme.median():.0f} rows) - check for gaps."
        )

    return findings


def explore_fund_master(fund_master: pd.DataFrame) -> list[str]:
    """Print + collect summary stats on fund_master categorical fields."""
    lines = []
    for col in ["fund_house", "category", "sub_category", "risk_category", "sebi_category_code"]:
        vals = fund_master[col].value_counts()
        print(f"\n{col} value counts:\n{vals}")
        lines.append(f"{col}: {dict(vals)}")
    return lines


def main() -> None:
    print("BLUESTOCK FINTECH - Day 1: Data Ingestion")
    print(f"Reading raw data from: {RAW_DIR}\n")

    frames: dict[str, pd.DataFrame] = {}
    summary_rows = []

    for filename in DATASETS:
        try:
            df = load_dataset(filename)
        except FileNotFoundError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            sys.exit(1)

        frames[filename] = df
        summary_rows.append(inspect(filename, df))

    # ---- Fund master exploration (Task 6) ----
    print(f"\n{'=' * 70}\nFUND MASTER EXPLORATION\n{'=' * 70}")
    fund_master_notes = explore_fund_master(frames["01_fund_master.csv"])

    # ---- AMFI code validation (Task 7) ----
    print(f"\n{'=' * 70}\nAMFI CODE VALIDATION\n{'=' * 70}")
    validation_notes = validate_amfi_codes(
        frames["01_fund_master.csv"], frames["02_nav_history.csv"]
    )
    for line in validation_notes:
        print(f"- {line}")

    # ---- Write data quality report (Task 3 + Task 7 output) ----
    summary_df = pd.DataFrame(summary_rows)
    report_path = REPORTS_DIR / "data_quality_report.txt"
    with open(report_path, "w") as f:
        f.write("BLUESTOCK FINTECH - Day 1 Data Quality Report\n")
        f.write("=" * 70 + "\n\n")
        f.write("Per-dataset summary\n")
        f.write("-" * 70 + "\n")
        f.write(summary_df.to_string(index=False))
        f.write("\n\n")
        f.write("Fund master category breakdown\n")
        f.write("-" * 70 + "\n")
        for line in fund_master_notes:
            f.write(line + "\n")
        f.write("\n")
        f.write("AMFI code validation (fund_master <-> nav_history)\n")
        f.write("-" * 70 + "\n")
        for line in validation_notes:
            f.write("- " + line + "\n")

    print(f"\nData quality report written to: {report_path}")
    print("\nDay 1 ingestion complete. All 10 datasets loaded successfully.")


if __name__ == "__main__":
    main()
