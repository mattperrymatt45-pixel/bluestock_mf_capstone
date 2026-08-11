# Power BI Build Guide — Bluestock MF Dashboard

**Why this guide exists:** `.pbix` is a proprietary binary format that only
Power BI Desktop (Windows/Mac) can write — it can't be generated from a
Linux script. The 4 PNG pages and `Dashboard.pdf` in this folder are
data-accurate mockups built from the same underlying data, showing exactly
what to build. Follow this guide in Power BI Desktop to produce the real
`bluestock_mf_dashboard.pbix` — should take 30-45 minutes.

## 1. Connect to data

**Option A — CSV import (simplest):** Home -> Get Data -> Text/CSV -> import
all 10 files from `data/processed/` (the `clean_*.csv` files) plus
`reports/performance_analytics/fund_scorecard.csv` and `alpha_beta.csv`.

**Option B — SQLite via ODBC:** install the SQLite ODBC driver, add a System
DSN pointing to `data/db/bluestock_mf.db`, then Get Data -> ODBC in Power
BI. This gives you all 11 tables (`dim_fund`, `dim_date`, `fact_nav`, etc.)
already modeled as a star schema — less relationship work in step 2.

Verify all tables loaded: Model view should show 8-11 tables depending on
which option you picked.

## 2. Build relationships

If you used Option A (flat CSVs), create these relationships in Model view
(Manage Relationships):

| From | To | Cardinality |
|---|---|---|
| `clean_02_nav_history[amfi_code]` | `clean_01_fund_master[amfi_code]` | Many-to-1 |
| `clean_08_investor_transactions[amfi_code]` | `clean_01_fund_master[amfi_code]` | Many-to-1 |
| `fund_scorecard[amfi_code]` | `clean_01_fund_master[amfi_code]` | 1-to-1 |
| `alpha_beta[amfi_code]` | `clean_01_fund_master[amfi_code]` | 1-to-1 |
| `clean_09_portfolio_holdings[amfi_code]` | `clean_01_fund_master[amfi_code]` | Many-to-1 |

For dates: add a dedicated Date table (Modeling -> New Table ->
`DateTable = CALENDAR(DATE(2022,1,1), DATE(2026,5,31))`), mark it as a
Date Table, and relate it to `date`/`transaction_date` columns across
`clean_02_nav_history`, `clean_08_investor_transactions`, and
`clean_10_benchmark_indices`. This is what lets one date slicer filter
every page at once.

## 3. Key DAX measures

Create these in a new measures table (Modeling -> New Table -> name it
`_Measures`, then add each as New Measure):

```dax
Total AUM (L Cr) = SUM(clean_03_aum_by_fund_house[aum_lakh_crore])

Latest SIP Inflow = 
CALCULATE(SUM(clean_04_monthly_sip_inflows[sip_inflow_crore]),
    clean_04_monthly_sip_inflows[month] = "2025-12")

Total Folios (Cr) = 
CALCULATE(SUM(clean_06_industry_folio_count[total_folios_crore]),
    clean_06_industry_folio_count[month] = "2025-12")

Avg Sharpe Ratio = AVERAGE(fund_scorecard[sharpe_ratio])

Total Transaction Amount = SUM(clean_08_investor_transactions[amount_inr])

Avg SIP Amount = 
CALCULATE(AVERAGE(clean_08_investor_transactions[amount_inr]),
    clean_08_investor_transactions[transaction_type] = "SIP")

Tracking Error % = 
STDEV.P(clean_02_nav_history[daily_return_pct]) * SQRT(252)
```

## 4. Build each page

Use the corresponding `pageN_*.png` in this folder as the visual reference
for layout, chart types, and the Bluestock colour theme. Chart-by-chart:

**Page 1 — Industry Overview**
- 4 Card visuals: Total AUM, Latest SIP Inflow, Total Folios, Schemes count (1,908 is a manual text card — it's an industry-wide AMFI figure, not derivable from the 40 tracked schemes)
- Line chart: `clean_03_aum_by_fund_house[date]` (axis) x `Total AUM` (value)
- Clustered bar chart: `fund_house` (axis) x `aum_lakh_crore` (value), sorted descending

**Page 2 — Fund Performance**
- Scatter chart: `std_dev_ann_pct` (X) x `return_3yr_pct` (Y), `aum_crore` (size), `category` (legend) — from `clean_07_scheme_performance` joined to `clean_01_fund_master[category]`
- Table/matrix visual: `fund_scorecard` columns (scheme_name, fund_house, cagr_3yr_pct, sharpe_ratio, alpha_annual_pct, fund_score) — enable sorting by clicking column headers (native Power BI table behavior)
- Line chart: NAV over time, 2 series (selected fund + Nifty 100) — use a "Top N" filter or a bookmark-driven selector for "selected fund"
- Slicers: `fund_house`, `category`, `plan`

**Page 3 — Investor Analytics**
- Bar chart: `state` (axis) x `Total Transaction Amount` (value)
- Donut chart: `transaction_type` (legend) x count
- Column chart: `age_group` (axis) x `Avg SIP Amount` (value)
- Line chart: month (axis) x transaction count, split by `transaction_type` (legend)
- Slicers: `state`, `age_group`, `city_tier`

**Page 4 — SIP & Market Trends**
- Combo chart (dual axis): `month` (axis), `sip_inflow_crore` (column, primary axis), Nifty 50 `close_value` (line, secondary axis)
- Bar chart: top 5 `category` by summed `net_inflow_crore`
- Matrix/heatmap: use a Matrix visual with `category` (rows), `month` (columns), `net_inflow_crore` (values), then apply conditional formatting (background color scale, red-yellow-green) via Format -> Cell elements -> Background color -> Color scale

## 5. Interactivity

- **Drill-through:** create a new page "Fund Detail", add a NAV line chart + key metrics table, drag `amfi_code` (or `scheme_name`) into the Drill-through filter well. Right-click any fund on the Page 2 scorecard table -> Drill Through -> Fund Detail.
- **Tooltips:** Format pane -> General -> Tooltips, or build a dedicated tooltip page (smaller canvas, e.g. NAV mini-chart) and set it as a custom tooltip on the scatter/line charts via Format -> Tooltip -> Report page tooltip.
- **Slicers:** sync slicers across pages if you want state/category filters to persist (View -> Sync Slicers pane).

## 6. Branding

Apply as a custom theme (View -> Themes -> Browse for themes, or paste as JSON via Customize current theme):

```json
{
  "name": "Bluestock Fintech",
  "dataColors": ["#1F3864", "#4472C4", "#8FAADC", "#D4A017", "#2E7D32", "#C0392B", "#7B5EA7", "#2E9E9E"],
  "background": "#FFFFFF",
  "foreground": "#1F3864",
  "tableAccent": "#1F3864"
}
```
Add the Bluestock wordmark/logo as an Image visual in the top-left of each
page header (matches the header bar in the reference PNGs).

## 7. Export

- File -> Save As -> `bluestock_mf_dashboard.pbix`
- File -> Export -> Export to PDF -> `Dashboard.pdf` (all 4 pages, replaces the mockup PDF in this folder)
- For PNG screenshots: File -> Export -> Export to PDF, then convert each PDF page to PNG (or use View -> Full Screen + Snipping Tool per page)

## What's already done for you

All the hard data work — cleaning, the SQLite star schema, the fund
scorecard, alpha/beta, tracking error — is already computed and sitting in
`data/processed/` and `reports/performance_analytics/`. This guide is
purely about the Power BI *presentation* layer; no further analysis is
needed before building the dashboard.
