-- ============================================================================
-- Bluestock Fintech - Mutual Fund Analytics Platform
-- Day 2, Task 6: Analytical SQL Queries
-- ============================================================================
-- Run against data/db/bluestock_mf.db
-- Tested via scripts/run_queries.py -> reports/query_results.txt
-- ============================================================================

-- Q1: Top 5 funds by AUM
-- --------------------------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    p.aum_crore
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.aum_crore DESC
LIMIT 5;


-- Q2: Average NAV per month (all schemes combined)
-- --------------------------------------------------------------------------
SELECT
    d.year,
    d.month,
    ROUND(AVG(n.nav), 2) AS avg_nav
FROM fact_nav n
JOIN dim_date d ON d.date_id = n.date_id
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- Q3: SIP inflow YoY growth (industry level, by month)
-- --------------------------------------------------------------------------
SELECT
    month,
    sip_inflow_crore,
    yoy_growth_pct
FROM fact_sip_industry
WHERE yoy_growth_pct IS NOT NULL
ORDER BY month;


-- Q4: Transactions by state (count + total amount)
-- --------------------------------------------------------------------------
SELECT
    state,
    COUNT(*) AS num_transactions,
    SUM(amount_inr) AS total_amount_inr
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_inr DESC;


-- Q5: Funds with expense_ratio < 1%
-- --------------------------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    f.expense_ratio_pct
FROM dim_fund f
WHERE f.expense_ratio_pct < 1.0
ORDER BY f.expense_ratio_pct ASC;


-- Q6: Top 5 funds by Sharpe ratio (best risk-adjusted return)
-- --------------------------------------------------------------------------
SELECT
    f.scheme_name,
    f.fund_house,
    p.sharpe_ratio,
    p.return_3yr_pct
FROM fact_performance p
JOIN dim_fund f ON f.amfi_code = p.amfi_code
ORDER BY p.sharpe_ratio DESC
LIMIT 5;


-- Q7: SIP vs Lumpsum vs Redemption split, overall
-- --------------------------------------------------------------------------
SELECT
    transaction_type,
    COUNT(*) AS num_transactions,
    SUM(amount_inr) AS total_amount_inr,
    ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM fact_transactions), 2) AS pct_of_transactions
FROM fact_transactions
GROUP BY transaction_type
ORDER BY total_amount_inr DESC;


-- Q8: Average SIP amount by age group
-- --------------------------------------------------------------------------
SELECT
    age_group,
    COUNT(*) AS num_sip_transactions,
    ROUND(AVG(amount_inr), 0) AS avg_sip_amount_inr
FROM fact_transactions
WHERE transaction_type = 'SIP'
GROUP BY age_group
ORDER BY avg_sip_amount_inr DESC;


-- Q9: AUM growth by fund house, year over year (latest snapshot per year)
-- --------------------------------------------------------------------------
SELECT
    a.fund_house,
    d.year,
    ROUND(AVG(a.aum_lakh_crore), 2) AS avg_aum_lakh_crore
FROM fact_aum a
JOIN dim_date d ON d.date_id = a.date_id
GROUP BY a.fund_house, d.year
ORDER BY a.fund_house, d.year;


-- Q10: Sector concentration - top 10 stock holdings by total market value
--      across all equity fund portfolios
-- --------------------------------------------------------------------------
SELECT
    stock_name,
    sector,
    COUNT(DISTINCT amfi_code) AS num_funds_holding,
    ROUND(SUM(market_value_cr), 2) AS total_market_value_cr
FROM fact_portfolio
GROUP BY stock_name, sector
ORDER BY total_market_value_cr DESC
LIMIT 10;
