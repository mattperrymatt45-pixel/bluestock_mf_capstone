"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 5: Dashboard Page 2 - Fund Performance (mockup)

Builds a Power-BI-style Page 2 as a static PNG: a return-vs-risk bubble
scatter (bubble size = AUM), a NAV-vs-Nifty-100 line chart for the top
scorecard fund, and a sortable-in-Power-BI fund scorecard table — all
sourced from the Day 4 performance analytics outputs. See
dashboard/POWER_BI_BUILD_GUIDE.md to reproduce this as a real Power BI page.

Usage:
    python scripts/build_dashboard_page2.py
"""
import sys
sys.path.insert(0, "/home/claude/bluestock_mf_capstone/scripts")
from dashboard_style import *
import pandas as pd
import numpy as np

PROJECT_ROOT = "/home/claude/bluestock_mf_capstone"
PROC = f"{PROJECT_ROOT}/data/processed"
PERF = f"{PROJECT_ROOT}/reports/performance_analytics"
OUT = f"{PROJECT_ROOT}/dashboard/pages"

fund_master = pd.read_csv(f"{PROC}/clean_01_fund_master.csv")
scheme_perf = pd.read_csv(f"{PROC}/clean_07_scheme_performance.csv")   # has aum_crore, std_dev_ann_pct
scorecard = pd.read_csv(f"{PERF}/fund_scorecard.csv")
nav_history = pd.read_csv(f"{PROC}/clean_02_nav_history.csv", parse_dates=["date"])
benchmark = pd.read_csv(f"{PROC}/clean_10_benchmark_indices.csv", parse_dates=["date"])

scatter_df = scheme_perf.drop(columns=["category"]).merge(fund_master[["amfi_code", "category"]], on="amfi_code")

fig = new_page("Fund Performance", "Page 2 of 4")

# Slicers
slicer_strip(fig, [0.015, 0.905, 0.45, 0.03], ["Fund House: All", "Category: All", "Plan: All"])

# Scatter: return vs risk, bubble = AUM
ax1 = panel(fig, [0.015, 0.48, 0.46, 0.40], "Return vs Risk (bubble size = AUM)")
cat_colors = {"Equity": PALETTE[0], "Debt": PALETTE[3], "Hybrid": PALETTE[4]}
for cat, sub in scatter_df.groupby("category"):
    ax1.scatter(sub["std_dev_ann_pct"], sub["return_3yr_pct"], s=sub["aum_crore"] / 40,
                color=cat_colors.get(cat, "grey"), alpha=0.65, edgecolor="white", linewidth=0.6, label=cat)
ax1.set_xlabel("Risk - Annualised Std Dev (%)", fontsize=8.5)
ax1.set_ylabel("3yr Return (%)", fontsize=8.5)
ax1.legend(fontsize=8, loc="lower right", frameon=True, framealpha=0.9)
ax1.tick_params(labelsize=8)
ax1.grid(alpha=0.25)

# NAV line vs benchmark - top scorecard fund
ax2 = panel(fig, [0.505, 0.48, 0.48, 0.40], "NAV vs Benchmark - Top Scored Fund (indexed, 3yr)")
top_fund_code = scorecard.iloc[0]["amfi_code"]
top_fund_name = scorecard.iloc[0]["scheme_name"]
nav_pivot = nav_history.pivot(index="date", columns="amfi_code", values="nav")
window_start = nav_pivot.index.max() - pd.DateOffset(years=3)
fund_s = nav_pivot[top_fund_code].loc[nav_pivot.index >= window_start]
n100 = benchmark[benchmark["index_name"] == "NIFTY100"].set_index("date")["close_value"].sort_index()
n100_s = n100.loc[n100.index >= window_start]
ax2.plot(fund_s.index, fund_s / fund_s.iloc[0] * 100, color=NAVY, linewidth=2, label=top_fund_name[:28])
ax2.plot(n100_s.index, n100_s / n100_s.iloc[0] * 100, color=ACCENT_GOLD, linewidth=2, linestyle="--", label="Nifty 100")
ax2.set_ylabel("Indexed (start=100)", fontsize=8.5)
ax2.legend(fontsize=7.5, loc="upper left", frameon=False)
ax2.tick_params(labelsize=8)
ax2.grid(alpha=0.25)

# Sortable fund scorecard table (top 12)
ax3 = panel(fig, [0.015, 0.05, 0.97, 0.36], "Fund Scorecard - Top 12 (sortable in Power BI: click column header)")
ax3.axis("off")
top12 = scorecard.head(12)[["overall_rank", "scheme_name", "fund_house", "cagr_3yr_pct", "sharpe_ratio", "alpha_annual_pct", "fund_score"]]
col_labels = ["Rank", "Scheme", "Fund House", "3yr Return %", "Sharpe", "Alpha %", "Score /100"]
cell_text = []
for _, r in top12.iterrows():
    cell_text.append([
        f"{int(r['overall_rank'])}", r["scheme_name"][:32], r["fund_house"].replace(" Mutual Fund", ""),
        f"{r['cagr_3yr_pct']:.1f}", f"{r['sharpe_ratio']:.2f}", f"{r['alpha_annual_pct']:.2f}", f"{r['fund_score']:.1f}",
    ])
tbl = ax3.table(cellText=cell_text, colLabels=col_labels, loc="center", cellLoc="left",
                 colWidths=[0.05, 0.34, 0.20, 0.12, 0.10, 0.10, 0.11])
tbl.auto_set_font_size(False)
tbl.set_fontsize(8.5)
tbl.scale(1, 1.55)
for (row, col), cell in tbl.get_celld().items():
    cell.set_edgecolor(CARD_BORDER)
    if row == 0:
        cell.set_facecolor(NAVY)
        cell.set_text_props(color="white", fontweight="bold")
    else:
        cell.set_facecolor("#F8F9FB" if row % 2 == 0 else "white")

fig.savefig(f"{OUT}/Dashboard_Page2_FundPerformance.png", dpi=150, bbox_inches=None, facecolor="white")
print("Saved Dashboard_Page2_FundPerformance.png")
