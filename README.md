# Bluestock Fintech — Mutual Fund Analytics Platform

Capstone project: end-to-end ETL pipeline, SQL data model, and interactive
dashboard for Indian mutual fund data (AMFI / mfapi.in / NSE / BSE sources).

> **Status:** Day 1 of 7 complete — project setup + data ingestion.

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

## Roadmap

| Day | Focus |
|---|---|
| 1 | Project setup + data ingestion *(this)* |
| 2 | Data cleaning + SQL database design |
| 3 | Exploratory data analysis |
| 4 | Fund performance & risk analytics |
| 5 | Power BI / Tableau dashboard |
| 6 | Advanced analytics + risk metrics |
| 7 | Final report + presentation |

## Disclaimer

This project is for educational purposes only and does not constitute
financial advice. Mutual fund investments are subject to market risks.
