"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 2, Task 5: Load cleaned data into SQLite

Creates data/db/bluestock_mf.db from sql/schema.sql, loads all 10 cleaned
CSVs from data/processed/ into their corresponding tables via
SQLAlchemy + df.to_sql(), builds dim_date from the full observed date range,
and verifies row counts against the source CSVs.

Usage:
    python scripts/load_to_db.py
"""

from pathlib import Path
import sqlite3
import sys
import pandas as pd
from sqlalchemy import create_engine, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DB_DIR = PROJECT_ROOT / "data" / "db"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "bluestock_mf.db"
SCHEMA_PATH = PROJECT_ROOT / "sql" / "schema.sql"


def build_dim_date(all_dates: pd.Series) -> pd.DataFrame:
    """Build dim_date covering every unique date seen across all fact CSVs."""
    dates = pd.to_datetime(all_dates.dropna().unique())
    df = pd.DataFrame({"date": sorted(dates)})
    df["date_id"] = df["date"].dt.strftime("%Y-%m-%d")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month
    df["quarter"] = df["date"].dt.quarter
    df["day_of_week"] = df["date"].dt.dayofweek
    df["is_weekday"] = (df["day_of_week"] < 5).astype(int)
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")
    return df[["date_id", "date", "year", "month", "quarter", "day_of_week", "is_weekday"]]


def main() -> None:
    print("BLUESTOCK FINTECH - Day 2, Task 5: Load cleaned data into SQLite")

    # Fresh DB each run for reproducibility
    if DB_PATH.exists():
        DB_PATH.unlink()

    # schema.sql contains multiple statements - SQLAlchemy's text() only
    # supports one statement per execute(), so use sqlite3's executescript
    # directly to apply the full DDL file.
    raw_conn = sqlite3.connect(DB_PATH)
    raw_conn.executescript(SCHEMA_PATH.read_text())
    raw_conn.commit()
    raw_conn.close()
    print(f"Schema created at {DB_PATH}")

    engine = create_engine(f"sqlite:///{DB_PATH}")

    # ---- Load each processed CSV ----
    fund_master = pd.read_csv(PROCESSED_DIR / "clean_01_fund_master.csv")
    nav_history = pd.read_csv(PROCESSED_DIR / "clean_02_nav_history.csv")
    aum = pd.read_csv(PROCESSED_DIR / "clean_03_aum_by_fund_house.csv")
    sip_industry = pd.read_csv(PROCESSED_DIR / "clean_04_monthly_sip_inflows.csv")
    category_inflows = pd.read_csv(PROCESSED_DIR / "clean_05_category_inflows.csv")
    folio = pd.read_csv(PROCESSED_DIR / "clean_06_industry_folio_count.csv")
    performance = pd.read_csv(PROCESSED_DIR / "clean_07_scheme_performance.csv")
    transactions = pd.read_csv(PROCESSED_DIR / "clean_08_investor_transactions.csv")
    portfolio = pd.read_csv(PROCESSED_DIR / "clean_09_portfolio_holdings.csv")
    benchmark = pd.read_csv(PROCESSED_DIR / "clean_10_benchmark_indices.csv")

    # ---- Build dim_date from every date column across fact sources ----
    all_dates = pd.concat([
        nav_history["date"], aum["date"], transactions["transaction_date"],
        portfolio["portfolio_date"], benchmark["date"],
    ])
    dim_date = build_dim_date(all_dates)

    source_row_counts = {
        "01_fund_master.csv": len(fund_master),
        "02_nav_history.csv": len(nav_history),
        "03_aum_by_fund_house.csv": len(aum),
        "04_monthly_sip_inflows.csv": len(sip_industry),
        "05_category_inflows.csv": len(category_inflows),
        "06_industry_folio_count.csv": len(folio),
        "07_scheme_performance.csv": len(performance),
        "08_investor_transactions.csv": len(transactions),
        "09_portfolio_holdings.csv": len(portfolio),
        "10_benchmark_indices.csv": len(benchmark),
    }

    # ---- Prepare frames to match table column names exactly ----
    fund_master_out = fund_master.rename(columns={})
    fund_master_out["amfi_code"] = fund_master_out["amfi_code"].astype(str)

    nav_out = nav_history.rename(columns={"date": "date_id"})
    nav_out["amfi_code"] = nav_out["amfi_code"].astype(str)

    aum_out = aum.rename(columns={"date": "date_id"})

    perf_out = performance.copy()
    perf_out["amfi_code"] = perf_out["amfi_code"].astype(str)
    perf_out["flag_negative_sharpe"] = perf_out["flag_negative_sharpe"].astype(int)
    perf_out["flag_expense_ratio_out_of_range"] = perf_out["flag_expense_ratio_out_of_range"].astype(int)
    # fact_performance only needs the performance-specific columns (fund
    # metadata lives in dim_fund already)
    perf_out = perf_out[[
        "amfi_code", "return_1yr_pct", "return_3yr_pct", "return_5yr_pct",
        "benchmark_3yr_pct", "alpha", "beta", "sharpe_ratio", "sortino_ratio",
        "std_dev_ann_pct", "max_drawdown_pct", "aum_crore", "expense_ratio_pct",
        "morningstar_rating", "risk_grade", "flag_negative_sharpe",
        "flag_expense_ratio_out_of_range",
    ]]

    tx_out = transactions.rename(columns={"transaction_date": "date_id"})
    tx_out["amfi_code"] = tx_out["amfi_code"].astype(str)

    portfolio_out = portfolio.rename(columns={})
    portfolio_out["amfi_code"] = portfolio_out["amfi_code"].astype(str)

    benchmark_out = benchmark.rename(columns={"date": "date_id"})

    # ---- Load into SQLite (append, since schema already has CREATE TABLE) ----
    table_loads = [
        ("dim_date", dim_date),
        ("dim_fund", fund_master_out),
        ("fact_nav", nav_out),
        ("fact_aum", aum_out),
        ("fact_sip_industry", sip_industry),
        ("fact_category_inflows", category_inflows),
        ("fact_folio", folio),
        ("fact_performance", perf_out),
        ("fact_transactions", tx_out),
        ("fact_portfolio", portfolio_out),
        ("fact_benchmark", benchmark_out),
    ]

    print("\nLoading tables:")
    for table_name, df in table_loads:
        df.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"  {table_name}: {len(df):,} rows loaded")

    # ---- Verify row counts match source CSVs ----
    print(f"\n{'=' * 70}\nVerifying row counts against source CSVs\n{'=' * 70}")
    verification = []
    check_map = {
        "01_fund_master.csv": "dim_fund",
        "02_nav_history.csv": "fact_nav",
        "03_aum_by_fund_house.csv": "fact_aum",
        "04_monthly_sip_inflows.csv": "fact_sip_industry",
        "05_category_inflows.csv": "fact_category_inflows",
        "06_industry_folio_count.csv": "fact_folio",
        "07_scheme_performance.csv": "fact_performance",
        "08_investor_transactions.csv": "fact_transactions",
        "09_portfolio_holdings.csv": "fact_portfolio",
        "10_benchmark_indices.csv": "fact_benchmark",
    }

    all_match = True
    with engine.connect() as conn:
        for csv_name, table in check_map.items():
            db_count = conn.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            source_count = source_row_counts[csv_name]
            match = db_count == source_count
            all_match &= match
            status = "OK" if match else "MISMATCH"
            print(f"  {csv_name:<32} source={source_count:>6,}  db[{table}]={db_count:>6,}  [{status}]")
            verification.append((csv_name, table, source_count, db_count, match))

    if all_match:
        print("\nAll table row counts match their source CSVs exactly.")
    else:
        print("\nWARNING: one or more tables do not match source row counts.", file=sys.stderr)

    print(f"\nDatabase ready: {DB_PATH} ({DB_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
