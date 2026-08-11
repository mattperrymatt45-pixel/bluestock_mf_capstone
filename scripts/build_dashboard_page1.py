import sys
sys.path.insert(0, "/home/claude/bluestock_mf_capstone/scripts")
from dashboard_style import *
import pandas as pd
import numpy as np

PROJECT_ROOT = "/home/claude/bluestock_mf_capstone"
PROC = f"{PROJECT_ROOT}/data/processed"
OUT = f"{PROJECT_ROOT}/dashboard/pages"

aum = pd.read_csv(f"{PROC}/clean_03_aum_by_fund_house.csv", parse_dates=["date"])
folio = pd.read_csv(f"{PROC}/clean_06_industry_folio_count.csv")
sip = pd.read_csv(f"{PROC}/clean_04_monthly_sip_inflows.csv")
sip["month_dt"] = pd.to_datetime(sip["month"], format="%Y-%m")

industry_aum = aum.groupby("date", as_index=False)["aum_lakh_crore"].sum()
aum["year"] = aum["date"].dt.year
aum_yearend = aum.sort_values("date").groupby(["fund_house", "year"], as_index=False).last()
aum_2025 = aum_yearend[aum_yearend["year"] == 2025].sort_values("aum_lakh_crore", ascending=True)

latest_folio = folio.iloc[-1]
latest_sip = sip.iloc[-1]
our_tracked_aum = aum[aum["date"] == aum["date"].max()]["aum_lakh_crore"].sum()

fig = new_page("Industry Overview", "Page 1 of 4")

# KPI cards
kpi_card(fig, [0.015, 0.77, 0.235, 0.13], "Rs. 81L Cr", "Industry Total AUM (AMFI, Dec 2025)", NAVY)
kpi_card(fig, [0.265, 0.77, 0.235, 0.13], f"Rs. {latest_sip['sip_inflow_crore']:,.0f} Cr", f"SIP Inflow ({latest_sip['month']}) - All-Time High", ACCENT_GOLD, delta="+17.2% YoY")
kpi_card(fig, [0.515, 0.77, 0.235, 0.13], f"{latest_folio['total_folios_crore']:.2f} Cr", f"Total Folios ({latest_folio['month']})", GREEN)
kpi_card(fig, [0.765, 0.77, 0.22, 0.13], "1,908", "Live Schemes (Industry, AMFI)", "#7B5EA7")

# Line chart: industry AUM trend (tracked 10 fund houses)
ax1 = panel(fig, [0.015, 0.40, 0.60, 0.34], "Industry AUM Trend - 10 Fund Houses Tracked (2022-2025)")
ax1.plot(industry_aum["date"], industry_aum["aum_lakh_crore"], color=NAVY, linewidth=2.2)
ax1.fill_between(industry_aum["date"], industry_aum["aum_lakh_crore"], alpha=0.12, color=NAVY)
ax1.set_ylabel("AUM (Rs. lakh crore)", fontsize=8.5)
ax1.tick_params(labelsize=8)
ax1.grid(alpha=0.25)

# Bar chart: AUM by AMC (2025 year-end)
ax2 = panel(fig, [0.635, 0.40, 0.35, 0.34], "AUM by Fund House (2025 Year-End)")
colors = [ACCENT_GOLD if fh == "SBI Mutual Fund" else "#9DB3D6" for fh in aum_2025["fund_house"]]
ax2.barh(aum_2025["fund_house"].str.replace(" Mutual Fund", ""), aum_2025["aum_lakh_crore"], color=colors)
ax2.set_xlabel("AUM (Rs. lakh crore)", fontsize=8.5)
ax2.tick_params(labelsize=7.5)
ax2.grid(alpha=0.25, axis="x")

# Folio growth mini chart
ax3 = panel(fig, [0.015, 0.05, 0.475, 0.30], "Total Folio Count Growth (Jan 2022 - Dec 2025)")
folio["month_dt"] = pd.to_datetime(folio["month"], format="%Y-%m")
ax3.plot(folio["month_dt"], folio["total_folios_crore"], color=GREEN, linewidth=2, marker="o", markersize=3)
ax3.fill_between(folio["month_dt"], folio["total_folios_crore"], alpha=0.10, color=GREEN)
ax3.set_ylabel("Folios (Cr)", fontsize=8.5)
ax3.tick_params(labelsize=8)
ax3.grid(alpha=0.25)

# SIP inflow mini chart
ax4 = panel(fig, [0.51, 0.05, 0.475, 0.30], "Monthly SIP Inflow (Jan 2022 - Dec 2025)")
ax4.plot(sip["month_dt"], sip["sip_inflow_crore"], color=ACCENT_GOLD, linewidth=2)
ax4.set_ylabel("SIP Inflow (Rs. Cr)", fontsize=8.5)
ax4.tick_params(labelsize=8)
ax4.grid(alpha=0.25)

fig.savefig(f"{OUT}/page1_industry_overview.png", dpi=150, bbox_inches=None, facecolor="white")
print("Saved page1_industry_overview.png")
