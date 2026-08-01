# Bluestock Fintech — Data Dictionary

Documents every column across all 10 source datasets and their corresponding
SQLite tables. Business definitions and source references follow the
project brief (AMFI India / mfapi.in / NSE / BSE public data).

---

## 1. `01_fund_master.csv` → table `dim_fund`

Master reference list of all 40 mutual fund schemes tracked in this project.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| amfi_code | TEXT (PK) | Unique AMFI scheme code identifying a specific scheme + plan (e.g. `125497` = HDFC Top 100 Direct) | AMFI India |
| fund_house | TEXT | Asset Management Company (AMC) name, e.g. SBI Mutual Fund | AMFI India |
| scheme_name | TEXT | Full official AMFI scheme name, including plan and option | AMFI India |
| category | TEXT | Broad SEBI category: Equity / Debt / Hybrid | AMFI India |
| sub_category | TEXT | Fund sub-category: Large Cap / Mid Cap / Small Cap / Liquid / Gilt etc. | AMFI India |
| plan | TEXT | Regular (via distributor, higher expense ratio) or Direct (no distributor commission) | AMFI India |
| launch_date | DATE | Date the scheme was launched | AMFI India |
| benchmark | TEXT | Official benchmark index the scheme is measured against | AMFI India |
| expense_ratio_pct | REAL | Annual expense ratio charged to investors, in % | AMFI India |
| exit_load_pct | REAL | Exit load % charged on early redemption (0 for most Liquid/Index funds) | AMFI India |
| min_sip_amount | INTEGER | Minimum monthly SIP investment amount, in INR | AMFI / AMC scheme document |
| min_lumpsum_amount | INTEGER | Minimum one-time lumpsum investment amount, in INR | AMFI / AMC scheme document |
| fund_manager | TEXT | Name of the primary fund manager | AMFI / AMC factsheet |
| risk_category | TEXT | SEBI riskometer category: Low / Moderate / High / Very High | AMFI / SEBI riskometer |
| sebi_category_code | TEXT | Internal SEBI category code (e.g. `EC01`=Large Cap, `DC01`=Liquid) | SEBI classification |

---

## 2. `02_nav_history.csv` → table `fact_nav`

Daily Net Asset Value for all 40 schemes, Jan 2022 – May 2026.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| amfi_code | TEXT (FK → dim_fund) | Scheme identifier | AMFI India |
| date_id | TEXT (FK → dim_date) | NAV date (business days only), ISO `YYYY-MM-DD` | AMFI / mfapi.in |
| nav | REAL | Net Asset Value per unit, in INR, anchored to real mfapi.in values | mfapi.in |
| daily_return_pct | REAL | Day-over-day % change in NAV, computed during Day 2 cleaning: `(nav_t / nav_t-1 - 1) * 100` | Derived |

---

## 3. `03_aum_by_fund_house.csv` → table `fact_aum`

Quarterly Assets Under Management by fund house, 2022–2025.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| fund_house | TEXT | Asset Management Company name | AMFI Quarterly Report |
| date_id | TEXT (FK → dim_date) | Quarter-end snapshot date | AMFI Quarterly Report |
| aum_lakh_crore | REAL | Total AUM in Rs. lakh crore (1 lakh crore = Rs. 10^12) | AMFI Quarterly Report |
| aum_crore | INTEGER | Total AUM in Rs. crore (1 crore = Rs. 10^7) — same figure, different unit | AMFI Quarterly Report |
| num_schemes | INTEGER | Number of live schemes offered by the fund house at that date | AMFI Quarterly Report |

---

## 4. `04_monthly_sip_inflows.csv` → table `fact_sip_industry`

Industry-wide monthly SIP metrics, Jan 2022 – Dec 2025.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| month | TEXT (PK) | Month in `YYYY-MM` format | AMFI Monthly Note |
| sip_inflow_crore | INTEGER | Total SIP inflows across the industry that month, in Rs. crore | AMFI Monthly Note |
| active_sip_accounts_crore | REAL | Number of SIP accounts with a contribution that month, in crore | AMFI Monthly Note |
| new_sip_accounts_lakh | REAL | New SIP registrations that month, in lakh accounts | AMFI Monthly Note |
| sip_aum_lakh_crore | REAL | Total assets held via SIP mode, in Rs. lakh crore | AMFI Monthly Note |
| yoy_growth_pct | REAL | Year-over-year % growth in `sip_inflow_crore`; null for the first 12 months (2022) since there's no prior year to compare | Derived |

---

## 5. `05_category_inflows.csv` → table `fact_category_inflows`

Net inflows by fund category, FY 2024–25.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| month | TEXT | Month in `YYYY-MM` format | AMFI Monthly Note |
| category | TEXT | Fund category: Large Cap / Mid Cap / Small Cap / ELSS / Liquid / etc. | AMFI Monthly Note |
| net_inflow_crore | REAL | Net inflow (inflows minus outflows) for that category that month, in Rs. crore | AMFI Monthly Note |

---

## 6. `06_industry_folio_count.csv` → table `fact_folio`

Total mutual fund investor folios, broken down by fund type.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| month | TEXT (PK) | Month in `YYYY-MM` format | AMFI / Business Standard |
| total_folios_crore | REAL | Total investor folios across the industry, in crore | AMFI |
| equity_folios_crore | REAL | Folios in Equity schemes, in crore | AMFI |
| debt_folios_crore | REAL | Folios in Debt schemes, in crore | AMFI |
| hybrid_folios_crore | REAL | Folios in Hybrid schemes, in crore | AMFI |
| others_folios_crore | REAL | Folios in other scheme types (e.g. Index, ETF, FoF), in crore | AMFI |

---

## 7. `07_scheme_performance.csv` → table `fact_performance`

Computed performance and risk metrics per scheme, as of the latest NAV date.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| amfi_code | TEXT (PK, FK → dim_fund) | Scheme identifier | Derived from NAV history |
| return_1yr_pct | REAL | 1-year absolute return, % | Derived |
| return_3yr_pct | REAL | 3-year CAGR, % | Derived |
| return_5yr_pct | REAL | 5-year CAGR, % | Derived |
| benchmark_3yr_pct | REAL | Benchmark index's 3-year CAGR, for comparison | Derived from benchmark_indices |
| alpha | REAL | Return above benchmark: `return_3yr_pct - benchmark_3yr_pct` | Derived |
| beta | REAL | Sensitivity to market movements (1.0 = moves with market) | Derived (OLS regression vs benchmark) |
| sharpe_ratio | REAL | Risk-adjusted return: `(Rp - Rf) / Std(Rp)`, annualised; higher is better, >1 is good | Derived |
| sortino_ratio | REAL | Like Sharpe but penalises only downside volatility | Derived |
| std_dev_ann_pct | REAL | Annualised standard deviation of daily returns, % | Derived |
| max_drawdown_pct | REAL | Worst peak-to-trough decline over the fund's history (negative value) | Derived |
| aum_crore | INTEGER | Scheme-level AUM, in Rs. crore | AMFI |
| expense_ratio_pct | REAL | Annual expense ratio, % | AMFI |
| morningstar_rating | INTEGER | 1–5 star rating (simulated in this dataset, based on Sharpe ratio) | Derived (simulated) |
| risk_grade | TEXT | SEBI riskometer category | AMFI / SEBI riskometer |
| flag_negative_sharpe | INTEGER (0/1) | Set during Day 2 cleaning: 1 if sharpe_ratio < 0 | Derived (Day 2 QA) |
| flag_expense_ratio_out_of_range | INTEGER (0/1) | Set during Day 2 cleaning: 1 if expense_ratio_pct falls outside the expected 0.1%–2.5% range | Derived (Day 2 QA) |

---

## 8. `08_investor_transactions.csv` → table `fact_transactions`

Individual SIP / Lumpsum / Redemption transactions across 5,000 simulated investors.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| tx_id | INTEGER (PK) | Surrogate transaction ID, auto-generated on load | Derived (Day 2 load) |
| investor_id | TEXT | Unique investor identifier, `INV000001`–`INV005000` | Simulated |
| amfi_code | TEXT (FK → dim_fund) | Scheme the transaction was made in | Simulated |
| date_id | TEXT (FK → dim_date) | Date of the transaction | Simulated |
| transaction_type | TEXT | SIP / Lumpsum / Redemption | Simulated |
| amount_inr | INTEGER | Transaction amount, in Indian Rupees | Simulated |
| state | TEXT | Investor's state (12 Indian states covered) | Simulated, based on real geographic distributions |
| city | TEXT | Investor's city | Simulated |
| city_tier | TEXT | T30 (Top 30 cities) or B30 (Beyond Top 30), per AMFI's official classification | AMFI classification |
| age_group | TEXT | 18-25 / 26-35 / 36-45 / 46-55 / 56+ | Simulated, based on real demographic distributions |
| gender | TEXT | Male / Female | Simulated |
| annual_income_lakh | REAL | Investor's annual income, in Rs. lakh | Simulated |
| payment_mode | TEXT | UPI / Net Banking / Mandate / Cheque | Simulated |
| kyc_status | TEXT | Verified (~92%) / Pending (~8%) | Simulated, based on real industry KYC completion rates |

---

## 9. `09_portfolio_holdings.csv` → table `fact_portfolio`

Top equity holdings for equity mutual funds, as of Dec 2025.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| amfi_code | TEXT (FK → dim_fund) | Scheme identifier | AMFI / AMC factsheet |
| stock_symbol | TEXT | NSE/BSE stock ticker symbol | NSE / BSE |
| stock_name | TEXT | Full company name | NSE / BSE |
| sector | TEXT | GICS-style sector classification (Banking, IT, FMCG, etc.) | NSE / BSE |
| weight_pct | REAL | % of the fund's portfolio allocated to this stock | AMC factsheet |
| market_value_cr | REAL | Market value of the holding, in Rs. crore | AMC factsheet |
| current_price_inr | REAL | Stock's current market price, in INR | NSE / BSE |
| portfolio_date | DATE | As-of date for the portfolio snapshot | AMC factsheet |

---

## 10. `10_benchmark_indices.csv` → table `fact_benchmark`

Daily closing values for benchmark indices used to compute Alpha/Beta/tracking error.

| Column | Type | Business Definition | Source |
|---|---|---|---|
| index_name | TEXT | Index name: Nifty 50, Nifty 100, Nifty Midcap 150, BSE SmallCap, CRISIL Liquid, CRISIL Gilt | NSE / BSE |
| date_id | TEXT (FK → dim_date) | Trading date | NSE / BSE |
| close_value | REAL | Index closing value on that date | NSE / BSE |

---

## Generated dimension: `dim_date`

Built during the Day 2 load (`scripts/load_to_db.py`) by taking every unique
date observed across `fact_nav`, `fact_aum`, `fact_transactions`,
`fact_portfolio`, and `fact_benchmark` — not sourced from a single CSV.

| Column | Type | Business Definition |
|---|---|---|
| date_id | TEXT (PK) | ISO date string, e.g. `2024-01-03` — also the join key used by fact tables |
| date | DATE | Same date, stored as SQLite DATE type |
| year | INTEGER | Calendar year |
| month | INTEGER | Calendar month (1–12) |
| quarter | INTEGER | Calendar quarter (1–4) |
| day_of_week | INTEGER | 0 = Monday … 6 = Sunday |
| is_weekday | INTEGER (0/1) | 1 if Mon–Fri, 0 if Sat/Sun |

---

## Notes on data authenticity

AMFI codes, fund names, fund houses, benchmarks, expense ratios, and AUM
figures are sourced from publicly available AMFI India data, mfapi.in, and
financial news sources. NAV values are anchored to real historical values.
Investor transaction data is synthetically generated but uses real
geographic, demographic, and behavioural distributions observed in the
Indian MF market. This project is for educational purposes only.
