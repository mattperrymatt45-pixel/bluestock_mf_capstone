"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 5: Dashboard Page 4 - SIP & Market Trends (mockup)

Builds a Power-BI-style Page 4 as a static PNG: a dual-axis SIP inflow vs
Nifty 50 chart, top 5 categories by FY25 net inflow, and a category inflow
heatmap — all from the cleaned SIP/category datasets. See
dashboard/POWER_BI_BUILD_GUIDE.md to reproduce this as a real Power BI page.

Usage:
    python scripts/build_dashboard_page4.py
"""
import sys
sys.path.insert(0, "/home/claude/bluestock_mf_capstone/scripts")
from dashboard_style import *
import pandas as pd
import numpy as np

PROJECT_ROOT = "/home/claude/bluestock_mf_capstone"
PROC = f"{PROJECT_ROOT}/data/processed"
OUT = f"{PROJECT_ROOT}/dashboard/pages"

sip = pd.read_csv(f"{PROC}/clean_04_monthly_sip_inflows.csv")
sip["month_dt"] = pd.to_datetime(sip["month"], format="%Y-%m")
benchmark = pd.read_csv(f"{PROC}/clean_10_benchmark_indices.csv", parse_dates=["date"])
category_inf = pd.read_csv(f"{PROC}/clean_05_category_inflows.csv")

nifty50 = benchmark[benchmark["index_name"] == "NIFTY50"].set_index("date")["close_value"].sort_index()
nifty50_monthly = nifty50.resample("MS").last()

fig = new_page("SIP & Market Trends", "Page 4 of 4")

# Dual-axis: SIP inflow (bar) + Nifty 50 (line)
ax1 = panel(fig, [0.075, 0.50, 0.51, 0.38], "SIP Inflow vs Nifty 50 (2022-2025)")
ax1.bar(sip["month_dt"], sip["sip_inflow_crore"], width=20, color="#B7C3DC", label="SIP Inflow (Rs. Cr)")
ax1.set_ylabel("SIP Inflow (Rs. Cr)", fontsize=8.5, color=NAVY)
ax1.tick_params(labelsize=8)
ax1b = ax1.twinx()
nifty_aligned = nifty50_monthly.reindex(sip["month_dt"]).ffill()
ax1b.plot(sip["month_dt"], nifty_aligned.values, color=ACCENT_GOLD, linewidth=2.2, label="Nifty 50")
ax1b.set_ylabel("Nifty 50", fontsize=8.5, color=ACCENT_GOLD)
ax1b.tick_params(labelsize=8)
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax1b.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="upper left", frameon=False)
ax1.grid(alpha=0.2)

# Top 5 categories by net inflow FY25
ax2 = panel(fig, [0.685, 0.50, 0.30, 0.38], "Top 5 Categories by Net Inflow (FY 2024-25)")
top5_cat = category_inf.groupby("category", as_index=False)["net_inflow_crore"].sum().sort_values("net_inflow_crore", ascending=False).head(5)
ax2.barh(top5_cat["category"][::-1], top5_cat["net_inflow_crore"][::-1], color=PALETTE[:5][::-1])
ax2.set_xlabel("Net Inflow (Rs. crore)", fontsize=8.5)
ax2.tick_params(labelsize=8.5)
ax2.grid(alpha=0.25, axis="x")

# Category inflow heatmap
ax3 = panel(fig, [0.075, 0.05, 0.905, 0.36], "Net Inflow by Category, FY 2024-25 (Rs. crore)")
cat_pivot = category_inf.pivot(index="category", columns="month", values="net_inflow_crore")
im = ax3.imshow(cat_pivot.values, cmap="RdYlGn", aspect="auto")
ax3.set_xticks(range(len(cat_pivot.columns)))
ax3.set_xticklabels(cat_pivot.columns, fontsize=7.5, rotation=0)
ax3.set_yticks(range(len(cat_pivot.index)))
ax3.set_yticklabels(cat_pivot.index, fontsize=8)
for i in range(cat_pivot.shape[0]):
    for j in range(cat_pivot.shape[1]):
        val = cat_pivot.values[i, j]
        ax3.text(j, i, f"{val:.0f}", ha="center", va="center", fontsize=6.5,
                  color="white" if abs(val) > cat_pivot.values.std() * 1.5 else "black")
cbar = fig.colorbar(im, ax=ax3, fraction=0.02, pad=0.01)
cbar.ax.tick_params(labelsize=7)

fig.savefig(f"{OUT}/Dashboard_Page4_SIPMarketTrends.png", dpi=150, bbox_inches=None, facecolor="white")
print("Saved Dashboard_Page4_SIPMarketTrends.png")
