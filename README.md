# Bluestock Fintech — Mutual Fund Analytics Platform

Capstone project: end-to-end ETL pipeline, SQL data model, and interactive
dashboard for Indian mutual fund data (AMFI / mfapi.in / NSE / BSE sources).

> **Status:** Day 6 of 7 complete — advanced analytics + risk metrics.

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

## Day 3 — Exploratory Data Analysis (EDA)

Open `notebooks/EDA_Analysis.ipynb` (or re-run it end to end):
```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/EDA_Analysis.ipynb
```
Generates 16 charts (target: 15+) across 9 analysis areas — NAV trends,
AUM growth, SIP inflows, category inflow heatmap, investor demographics,
geographic distribution, folio growth, NAV return correlation, and sector
allocation — plus a markdown summary of 10 key findings. All charts are
saved as PNG to `notebooks/charts/` for the final report.

### Day 3 findings (honest version)

- **2023 was a genuine broad-based rally** (+15.7% average NAV across all
  40 schemes) but **2024 was a slowdown, not a correction** — growth
  continued, just more slowly (+4.1% in the back half), and the average
  NAV series never drops more than ~1% from its running peak across the
  full 4.5-year window. Individual funds do show real dips in that window
  (see Chart 2), even though the aggregate stays positive.
- SBI Mutual Fund holds the largest AUM among the 10 fund houses tracked
  (Rs. 12.50 lakh crore, FY25), consistent with its real-world position.
- SIP inflows peaked at their all-time high in December 2025.
- SIP amounts are **fairly flat across age groups** (~6% spread, 56+
  slightly ahead) — not the strong mid-career skew a first glance might
  suggest.
- Geographic SIP value is **fairly evenly spread across states**
  (Rs. 1.6-2.1 Cr each) — no dominant outlier state in this dataset. T30
  cities still hold 67% of investors vs. 33% B30.
- **NAV return correlations across funds are near-zero, even within the
  same category** (strongest pair: 0.07) — flagged as a data-generation
  limitation rather than a real market pattern, since real large-cap
  equity funds typically correlate 0.85+ via shared market beta.
- Sector allocation is genuinely concentrated: Banking alone is ~19% of
  aggregate portfolio value across all equity funds.

## Day 4 — Fund Performance Analytics

Open `notebooks/Performance_Analytics.ipynb` (or re-run it end to end):
```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/Performance_Analytics.ipynb
```
Computes daily returns, CAGR (1yr/3yr/max-available), Sharpe and Sortino
ratios (Rf = 6.5%), Alpha/Beta vs Nifty 100 (via `scipy.stats.linregress`),
Maximum Drawdown, a composite 0-100 Fund Scorecard, and a benchmark
comparison chart with tracking error. All outputs go to
`reports/performance_analytics/`, including the three required
deliverables: `alpha_beta.csv`, `fund_scorecard.csv`, and
`benchmark_chart.png`.

### Day 4 findings (honest version)

- Daily returns validate cleanly: no NaN/Inf, no single-day move beyond
  ±10%, pooled distribution is unimodal and centred near zero.
- The dataset only covers **~4.4 years** of NAV history (Jan 2022 - May
  2026), so a true 5-year CAGR isn't computable — the "5yr" column uses
  the maximum available lookback instead, clearly labelled rather than
  faked.
- **Alpha/Beta regressions against Nifty 100 have essentially no
  explanatory power** — average R² across all 40 funds is 0.0006, max is
  0.0028. This lines up with Day 3's finding that fund-to-fund NAV
  correlations were also near zero: the simulated NAV series behave like
  independent random walks rather than being driven by a shared market
  factor. In a real market, Equity Large Cap funds would typically show
  R² of 0.7-0.9+ against Nifty 100. Alpha/Beta values here are
  mathematically correct (formula followed exactly as specified) but
  carry very little statistical signal.
- Computed Sharpe/Alpha/3yr-return **don't strongly agree** with the
  pre-supplied `scheme_performance.csv` figures (correlations of -0.33,
  -0.20, and +0.08 respectively) — most likely because that file was
  generated with different assumptions (different benchmark per fund,
  different risk-free rate, or different lookback) that aren't documented
  in the dataset. Recommendation carried into the notebook: treat this
  notebook's numbers as authoritative for the final report, since every
  assumption here is fully transparent, and treat `scheme_performance.csv`
  as a reference dataset rather than ground truth.
- The Fund Scorecard produces a sensible 0-100 spread (16.2 to 88.2 across
  40 funds) despite the Alpha weakness above, since 3 of its 5 weighted
  components (3yr return, expense ratio, max drawdown) don't depend on
  the benchmark regression.

## Day 5 — Dashboard (Power BI)

**Important limitation:** this environment has no Power BI or Tableau
installed (Linux sandbox, no Windows desktop apps) — `.pbix` is a
proprietary binary only Power BI Desktop can write, so it can't be
generated by a script here. What's actually delivered instead:

1. **4 dashboard mockup pages** (`dashboard/pages/Dashboard_Page1-4_*.png`)
   — built with matplotlib from the real cleaned data (not placeholders),
   styled to match a genuine Power BI look: navy header bar, KPI cards,
   chart panels, slicer-pill UI elements.
   - Page 1: Industry Overview — KPI cards, AUM trend, AUM by AMC, folio growth, SIP trend
   - Page 2: Fund Performance — return-vs-risk scatter, NAV vs benchmark, sortable scorecard table
   - Page 3: Investor Analytics — state bar chart, transaction type donut, SIP-by-age, monthly volume
   - Page 4: SIP & Market Trends — dual-axis SIP/Nifty 50, top categories, category heatmap
2. **`dashboard/Dashboard.pdf`** — all 4 pages compiled into one PDF.
3. **`dashboard/POWER_BI_BUILD_GUIDE.md`** — complete step-by-step guide
   (data connections, relationships, DAX measures, chart-by-chart build
   instructions, Bluestock theme JSON, drill-through/tooltip setup, export
   steps) to build the real `bluestock_mf_dashboard.pbix` in Power BI
   Desktop — roughly 30-45 minutes, since all the underlying data work
   (cleaning, star schema, scorecard, alpha/beta) is already done.

### Day 5 findings / fixes caught during build

- `clean_07_scheme_performance.csv`'s `category` column is actually
  sub-category data (Large Cap, Small Cap, Gilt, etc., 12 values) rather
  than the broad Equity/Debt/Hybrid split — caught this before building
  the Page 2 scatter chart and merged in the correct `category` from
  `clean_01_fund_master` instead of mislabeling the legend.
- Several panel layouts initially clipped axis/tick labels against the
  figure edge (state names cut off, y-axis numbers cropped) — fixed by
  adjusting panel positions to leave margin for labels rather than
  cropping them out of the final image.

## Day 6 — Advanced Analytics + Risk Metrics

Open `notebooks/Advanced_Analytics.ipynb` (or re-run it end to end):
```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/Advanced_Analytics.ipynb
```
Computes Historical VaR/CVaR (95%) for all 40 schemes, rolling 90-day
Sharpe for the top 5 scorecard funds, investor cohort analysis (by first
transaction year), SIP continuity/at-risk flagging, a standalone fund
recommender (`scripts/recommender.py`), and sector concentration (HHI)
across all 34 equity funds. Outputs go to `reports/advanced_analytics/`.

**Recommender usage:**
```bash
python scripts/recommender.py --risk Moderate
```
Returns the top 3 funds by Sharpe ratio within the matching SEBI risk
category (Low / Moderate / High — exact match, so "Moderately High" and
"Very High" funds aren't returned by either neighbouring level; documented
as a deliberate simple design choice in the script's docstring).

### Day 6 findings (honest version)

- **SBI Small Cap Fund (Direct) has the worst 5% VaR** of all 40 schemes
  (-2.69% on a bad day), while ICICI Pru Liquid Fund is the mildest
  (-0.02%) — VaR ranking tracks sub-category risk closely, Small/Mid Cap
  clustering high and Liquid/Gilt clustering low, as expected.
- Rolling 90-day Sharpe for the top 5 scorecard funds oscillates between
  roughly +4 and -4 with no persistent trend — consistent with the
  near-zero market correlation found on Day 3/4, since a fund with no
  stable relationship to a market factor will show a noisy, mean-reverting
  Sharpe rather than a smooth one.
- **The SIP "at-risk" flag (>35-day gap) fires on 97.8% of eligible
  investors** — too high to be a meaningful signal. The underlying cause
  is transparent: eligible investors only have 6-12 total SIP transactions
  logged across the ~4.4-year window, with a median gap of ~65 days, so
  the simulated SIP cadence in this dataset is roughly bi-monthly-or-sparser
  rather than strict monthly. The 35-day rule is the right threshold for a
  *true* monthly SIP; it just doesn't discriminate well on this dataset's
  actual spacing. Flagged explicitly rather than reported as "98% of
  investors are lapsing."
- 2024-cohort investors invested far more in aggregate than the 2025
  cohort (Rs. 349.1 Cr vs. a much smaller total) — this reflects cohort
  *tenure* (more time in the dataset to transact), not cohort quality.
- Sector/stock concentration (HHI) ranges narrowly across equity funds,
  with no fund showing dangerous single-stock concentration in this
  dataset — see `sector_hhi_chart.png` for the full ranking.

## Roadmap

| Day | Focus |
|---|---|
| 1 | Project setup + data ingestion ✅ |
| 2 | Data cleaning + SQL database design ✅ |
| 3 | Exploratory data analysis ✅ |
| 4 | Fund performance & risk analytics ✅ |
| 5 | Power BI / Tableau dashboard ✅ |
| 6 | Advanced analytics + risk metrics *(this)* |
| 7 | Final report + presentation |

## Disclaimer

This project is for educational purposes only and does not constitute
financial advice. Mutual fund investments are subject to market risks.
