"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 6, Task 5: Simple Fund Recommender

Given a risk appetite (Low / Moderate / High), recommends the top 3 funds
by Sharpe ratio within the matching `risk_category` from fund_master.

Risk categories in the dataset are the SEBI riskometer grades: Low,
Moderate, Moderately High, High, Very High. This recommender uses an exact
string match on the three levels requested by the task brief - so "High"
only matches funds tagged exactly "High" (not "Very High"), and
"Moderately High" funds are not returned by either "Moderate" or "High".
That's a deliberate, simple design choice worth knowing about rather than
a silent gap: a production version would probably want an explicit
mapping table instead of exact-match strings.

Usage (as a script):
    python scripts/recommender.py --risk Moderate

Usage (as a module):
    from recommender import recommend_funds
    recommend_funds("Moderate", fund_master_df, scorecard_df)
"""

import argparse
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PERF_DIR = PROJECT_ROOT / "reports" / "performance_analytics"

VALID_RISK_LEVELS = ["Low", "Moderate", "High"]


def recommend_funds(risk_appetite: str, fund_master: pd.DataFrame, scorecard: pd.DataFrame, top_n: int = 3) -> pd.DataFrame:
    """Return the top N funds by Sharpe ratio within the matching risk_category.

    Parameters
    ----------
    risk_appetite : "Low", "Moderate", or "High" (case-insensitive)
    fund_master    : cleaned fund master dataframe (needs amfi_code, risk_category, scheme_name, fund_house)
    scorecard      : Day 4 fund_scorecard dataframe (needs amfi_code, sharpe_ratio)
    top_n          : number of funds to return (default 3)
    """
    normalised = risk_appetite.strip().capitalize()
    if normalised not in VALID_RISK_LEVELS:
        raise ValueError(f"risk_appetite must be one of {VALID_RISK_LEVELS}, got '{risk_appetite}'")

    matching = fund_master[fund_master["risk_category"] == normalised]
    if matching.empty:
        return pd.DataFrame(columns=["scheme_name", "fund_house", "risk_category", "sharpe_ratio"])

    merged = matching.merge(scorecard[["amfi_code", "sharpe_ratio"]], on="amfi_code", how="inner")
    top = merged.sort_values("sharpe_ratio", ascending=False).head(top_n)
    return top[["scheme_name", "fund_house", "risk_category", "sharpe_ratio"]].reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Recommend top mutual funds by risk appetite.")
    parser.add_argument("--risk", required=True, choices=VALID_RISK_LEVELS,
                         help="Investor risk appetite: Low, Moderate, or High")
    parser.add_argument("--top", type=int, default=3, help="Number of funds to recommend (default 3)")
    args = parser.parse_args()

    fund_master = pd.read_csv(PROCESSED_DIR / "clean_01_fund_master.csv")
    scorecard = pd.read_csv(PERF_DIR / "fund_scorecard.csv")

    result = recommend_funds(args.risk, fund_master, scorecard, top_n=args.top)

    print(f"\nTop {args.top} funds for '{args.risk}' risk appetite (ranked by Sharpe ratio):\n")
    if result.empty:
        print("No funds found matching this risk category.")
    else:
        print(result.to_string(index=False))


if __name__ == "__main__":
    main()
