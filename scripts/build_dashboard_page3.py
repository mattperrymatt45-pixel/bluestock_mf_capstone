"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 5: Dashboard Page 3 - Investor Analytics (mockup)

Builds a Power-BI-style Page 3 as a static PNG: transaction amount by
state, a transaction-type donut, average SIP amount by age group, and
monthly transaction volume by type — all from the cleaned investor
transactions data. See dashboard/POWER_BI_BUILD_GUIDE.md to reproduce this
as a real Power BI page.

Usage:
    python scripts/build_dashboard_page3.py
"""
import sys
from pathlib import Path
PROJECT_ROOT_PATH = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT_PATH / "scripts"))
from dashboard_style import *
import pandas as pd
import numpy as np

PROJECT_ROOT = str(PROJECT_ROOT_PATH)
PROC = f"{PROJECT_ROOT}/data/processed"
OUT = f"{PROJECT_ROOT}/dashboard/pages"

tx = pd.read_csv(f"{PROC}/clean_08_investor_transactions.csv", parse_dates=["transaction_date"])

fig = new_page("Investor Analytics", "Page 3 of 4")

# Slicers
slicer_strip(fig, [0.015, 0.905, 0.45, 0.03], ["State: All", "Age Group: All", "City Tier: All"])

# Bar: transaction amount by state
ax1 = panel(fig, [0.075, 0.50, 0.40, 0.38], "Total Transaction Amount by State")
state_amt = tx.groupby("state", as_index=False)["amount_inr"].sum().sort_values("amount_inr", ascending=True)
ax1.barh(state_amt["state"], state_amt["amount_inr"] / 1e7, color=NAVY)
ax1.set_xlabel("Amount (Rs. crore)", fontsize=8.5)
ax1.tick_params(labelsize=7)
ax1.grid(alpha=0.25, axis="x")

# Donut: transaction type split
ax2 = panel(fig, [0.505, 0.50, 0.20, 0.38], "Transaction Type Split")
tx_type = tx["transaction_type"].value_counts()
ax2.pie(tx_type, labels=tx_type.index, autopct="%1.0f%%", startangle=90,
        colors=[NAVY, ACCENT_GOLD, "#8FAADC"], wedgeprops=dict(width=0.42, edgecolor="white"),
        textprops={"fontsize": 7.5}, radius=0.9)
ax2.set_title("", fontsize=1)

# Bar: age group vs avg SIP amount
ax3 = panel(fig, [0.80, 0.50, 0.18, 0.38], "Avg SIP Amount by Age")
sip_tx = tx[tx["transaction_type"] == "SIP"]
order = ["18-25", "26-35", "36-45", "46-55", "56+"]
avg_sip = sip_tx.groupby("age_group")["amount_inr"].mean().reindex(order)
ax3.bar(avg_sip.index, avg_sip.values, color=PALETTE[1])
ax3.set_ylabel("Avg SIP (Rs.)", fontsize=7.5)
ax3.tick_params(labelsize=7, axis="x", rotation=30)
ax3.tick_params(labelsize=7, axis="y")
ax3.grid(alpha=0.25, axis="y")

# Line: monthly transaction volume
ax4 = panel(fig, [0.075, 0.05, 0.905, 0.36], "Monthly Transaction Volume (count, by type)")
tx["month"] = tx["transaction_date"].dt.to_period("M").dt.to_timestamp()
monthly = tx.groupby(["month", "transaction_type"]).size().unstack(fill_value=0)
for i, col in enumerate(monthly.columns):
    ax4.plot(monthly.index, monthly[col], label=col, color=PALETTE[i], linewidth=1.8)
ax4.set_ylabel("Transaction Count", fontsize=8.5)
ax4.legend(fontsize=8, loc="center left", frameon=False)
ax4.tick_params(labelsize=8)
ax4.grid(alpha=0.25)

fig.savefig(f"{OUT}/Dashboard_Page3_InvestorAnalytics.png", dpi=150, bbox_inches=None, facecolor="white")
print("Saved Dashboard_Page3_InvestorAnalytics.png")
