# Bluestock Fintech — Mutual Fund Analytics Platform

Capstone project: end-to-end ETL pipeline, SQL data model, and interactive
dashboard for Indian mutual fund data (AMFI / mfapi.in / NSE / BSE sources).

> **Status:** Day 2 of 7 complete — data cleaning + SQL database design.

## Data note

The 10 source CSVs (`data/raw/`) were provided directly for this project.
Per the project brief, NAV values are anchored to real AMFI/mfapi.in figures
and investor transaction data is synthetically generated using realistic
Indian MF market distributions. See the capstone PDF, Appendix 8, for the
full schema reference and data-authenticity note.

## Folder structure

```
bluestock_mf_capstone/
├── data/
│   ├── raw/            # Original 10 CSVs + live/ (mfapi.in pulls)
│   ├── processed/       # Cleaned/merged CSVs (Day 2+)
│   └── db/              # bluestock_mf.db (SQLite, Day 2+)
├── notebooks/            # EDA / analytics notebooks (Day 3+)
├── scripts/
│   ├── data_ingestion.py    # Day 1: load & inspect all 10 CSVs
│   └── live_nav_fetch.py    # Day 1: pull live NAV from mfapi.in
├── sql/                  # schema.sql, queries.sql (Day 2+)
├── dashboard/             # Power BI / Tableau file (Day 5+)
├── reports/               # data_quality_report.txt, Final_Report.pdf
└── requirements.txt
```

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Day 1 — Project Setup + Data Ingestion

1. Load and inspect all 10 provided CSVs:
   ```bash
   python scripts/data_ingestion.py
   ```
   Prints shape/dtypes/head for each dataset, explores `fund_master`
   categories, validates that every AMFI code in `fund_master` has matching
   `nav_history` rows, and writes `reports/data_quality_report.txt`.

2. Fetch live NAV data from the public mfapi.in API (no auth required):
   ```bash
   python scripts/live_nav_fetch.py
   ```
   Pulls HDFC Top 100 plus 5 selected large-cap schemes and saves each as a
   raw CSV under `data/raw/live/`. Requires outbound access to
   `api.mfapi.in`.

### Day 1 findings

- All 10 datasets load cleanly: 0 duplicate rows across every file.
- Only `04_monthly_sip_inflows.csv` has nulls (12, in `yoy_growth_pct`) —
  expected, since the first 12 months (2022) have no prior year to compare
  against.
- All 40 AMFI codes in `fund_master` have exactly matching NAV history
  (1,150 rows each, no gaps) — see `reports/data_quality_report.txt`.

## Day 2 — Data Cleaning + SQL Database Design

1. Clean all 10 datasets and write results to `data/processed/`:
   ```bash
   python scripts/clean_data.py
   ```
   Deep cleaning logic for `nav_history` (date parsing, sort, dedup,
   forward-fill for holidays, NAV > 0 validation), `investor_transactions`
   (standardise transaction_type, fix dates, validate amount > 0, check KYC
   enum), and `scheme_performance` (numeric validation, negative-Sharpe and
   expense-ratio-range flags). The remaining 7 datasets get baseline cleaning
   (trim, date parsing, dedup). Log written to `reports/cleaning_log.txt`.

2. Load the cleaned CSVs into SQLite:
   ```bash
   python scripts/load_to_db.py
   ```
   Applies `sql/schema.sql` (2 dimension + 9 fact tables) to a fresh
   `data/db/bluestock_mf.db`, loads all 10 cleaned datasets via
   SQLAlchemy + `df.to_sql()`, builds `dim_date` from the observed date
   range, and verifies every table's row count against its source CSV.

3. Run the 10 analytical queries:
   ```bash
   python scripts/run_queries.py
   ```
   Executes `sql/queries.sql` against the database and writes results to
   `reports/query_results.txt`.

### Day 2 findings

- All 10 datasets cleaned with **zero rows dropped** — the source data had
  no invalid NAVs, no bad enum values, no out-of-range expense ratios, and
  no unparseable dates.
- `nav_history` already covers every business day per scheme with no gaps,
  so the forward-fill logic runs but has nothing to fill (0 values filled)
  — logic is in place and will activate automatically if real AMFI holiday
  gaps are introduced later.
- All 11 tables (`dim_fund`, `dim_date`, `fact_nav`, `fact_aum`,
  `fact_sip_industry`, `fact_category_inflows`, `fact_folio`,
  `fact_performance`, `fact_transactions`, `fact_portfolio`,
  `fact_benchmark`) load with row counts matching their source CSVs exactly.
- See `data_dictionary.md` for full column-level documentation.

## Roadmap

| Day | Focus |
|---|---|
| 1 | Project setup + data ingestion ✅ |
| 2 | Data cleaning + SQL database design *(this)* |
| 3 | Exploratory data analysis |
| 4 | Fund performance & risk analytics |
| 5 | Power BI / Tableau dashboard |
| 6 | Advanced analytics + risk metrics |
| 7 | Final report + presentation |

## Disclaimer

This project is for educational purposes only and does not constitute
financial advice. Mutual fund investments are subject to market risks.
