-- ============================================================================
-- Bluestock Fintech - Mutual Fund Analytics Platform
-- Day 2, Task 4: SQLite Star Schema
-- ============================================================================
-- Star schema: 2 dimension tables + 9 fact tables, covering all 10 source
-- CSVs. amfi_code is the conformed dimension key joining fund-level facts;
-- date is the conformed key joining time-series facts via dim_date.
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ----------------------------------------------------------------------------
-- DIMENSION: dim_fund  (source: 01_fund_master.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code           TEXT PRIMARY KEY,
    fund_house          TEXT NOT NULL,
    scheme_name         TEXT NOT NULL,
    category            TEXT,               -- Equity / Debt / Hybrid
    sub_category        TEXT,               -- Large Cap / Mid Cap / Liquid / etc.
    plan                TEXT,               -- Regular / Direct
    launch_date         DATE,
    benchmark           TEXT,
    expense_ratio_pct   REAL,
    exit_load_pct       REAL,
    min_sip_amount      INTEGER,
    min_lumpsum_amount  INTEGER,
    fund_manager        TEXT,
    risk_category       TEXT,               -- Low / Moderate / High / Very High
    sebi_category_code  TEXT
);

-- ----------------------------------------------------------------------------
-- DIMENSION: dim_date  (generated - covers full range across all fact tables)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_id      TEXT PRIMARY KEY,          -- ISO date string, e.g. '2024-01-03'
    date         DATE NOT NULL,
    year         INTEGER NOT NULL,
    month        INTEGER NOT NULL,
    quarter      INTEGER NOT NULL,
    day_of_week  INTEGER NOT NULL,          -- 0=Monday ... 6=Sunday
    is_weekday   INTEGER NOT NULL           -- 1 = Mon-Fri, 0 = Sat/Sun
);

-- ----------------------------------------------------------------------------
-- FACT: fact_nav  (source: 02_nav_history.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_nav (
    amfi_code        TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    date_id          TEXT NOT NULL REFERENCES dim_date(date_id),
    nav              REAL NOT NULL,
    daily_return_pct REAL,
    PRIMARY KEY (amfi_code, date_id)
);

-- ----------------------------------------------------------------------------
-- FACT: fact_aum  (source: 03_aum_by_fund_house.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_aum (
    fund_house       TEXT NOT NULL,
    date_id          TEXT NOT NULL REFERENCES dim_date(date_id),
    aum_lakh_crore   REAL,
    aum_crore        INTEGER,
    num_schemes      INTEGER,
    PRIMARY KEY (fund_house, date_id)
);

-- ----------------------------------------------------------------------------
-- FACT: fact_sip_industry  (source: 04_monthly_sip_inflows.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_sip_industry (
    month                       TEXT PRIMARY KEY,  -- 'YYYY-MM'
    sip_inflow_crore            INTEGER,
    active_sip_accounts_crore   REAL,
    new_sip_accounts_lakh       REAL,
    sip_aum_lakh_crore          REAL,
    yoy_growth_pct              REAL
);

-- ----------------------------------------------------------------------------
-- FACT: fact_category_inflows  (source: 05_category_inflows.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_category_inflows (
    month             TEXT NOT NULL,
    category          TEXT NOT NULL,
    net_inflow_crore  REAL,
    PRIMARY KEY (month, category)
);

-- ----------------------------------------------------------------------------
-- FACT: fact_folio  (source: 06_industry_folio_count.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_folio (
    month                  TEXT PRIMARY KEY,
    total_folios_crore     REAL,
    equity_folios_crore    REAL,
    debt_folios_crore      REAL,
    hybrid_folios_crore    REAL,
    others_folios_crore    REAL
);

-- ----------------------------------------------------------------------------
-- FACT: fact_performance  (source: 07_scheme_performance.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_performance (
    amfi_code                     TEXT PRIMARY KEY REFERENCES dim_fund(amfi_code),
    return_1yr_pct                REAL,
    return_3yr_pct                REAL,
    return_5yr_pct                REAL,
    benchmark_3yr_pct              REAL,
    alpha                          REAL,
    beta                           REAL,
    sharpe_ratio                   REAL,
    sortino_ratio                  REAL,
    std_dev_ann_pct                REAL,
    max_drawdown_pct               REAL,
    aum_crore                      INTEGER,
    expense_ratio_pct              REAL,
    morningstar_rating             INTEGER,
    risk_grade                     TEXT,
    flag_negative_sharpe            INTEGER,   -- 0/1, set during Day 2 cleaning
    flag_expense_ratio_out_of_range INTEGER    -- 0/1, set during Day 2 cleaning
);

-- ----------------------------------------------------------------------------
-- FACT: fact_transactions  (source: 08_investor_transactions.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_transactions (
    tx_id               INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT NOT NULL,
    amfi_code           TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    date_id             TEXT NOT NULL REFERENCES dim_date(date_id),
    transaction_type    TEXT NOT NULL,        -- SIP / Lumpsum / Redemption
    amount_inr          INTEGER NOT NULL,
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,                 -- T30 / B30
    age_group           TEXT,
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,
    kyc_status          TEXT
);

-- ----------------------------------------------------------------------------
-- FACT: fact_portfolio  (source: 09_portfolio_holdings.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_portfolio (
    amfi_code           TEXT NOT NULL REFERENCES dim_fund(amfi_code),
    stock_symbol        TEXT NOT NULL,
    stock_name          TEXT,
    sector              TEXT,
    weight_pct          REAL,
    market_value_cr     REAL,
    current_price_inr   REAL,
    portfolio_date      DATE,
    PRIMARY KEY (amfi_code, stock_symbol, portfolio_date)
);

-- ----------------------------------------------------------------------------
-- FACT: fact_benchmark  (source: 10_benchmark_indices.csv)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_benchmark (
    index_name    TEXT NOT NULL,
    date_id       TEXT NOT NULL REFERENCES dim_date(date_id),
    close_value   REAL,
    PRIMARY KEY (index_name, date_id)
);

-- ----------------------------------------------------------------------------
-- Indexes for fast query performance (amfi_code, date lookups)
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_fact_nav_date            ON fact_nav(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_nav_amfi             ON fact_nav(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_transactions_amfi    ON fact_transactions(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_transactions_date    ON fact_transactions(date_id);
CREATE INDEX IF NOT EXISTS idx_fact_transactions_state   ON fact_transactions(state);
CREATE INDEX IF NOT EXISTS idx_fact_aum_house            ON fact_aum(fund_house);
CREATE INDEX IF NOT EXISTS idx_fact_portfolio_amfi       ON fact_portfolio(amfi_code);
CREATE INDEX IF NOT EXISTS idx_fact_benchmark_index      ON fact_benchmark(index_name);
