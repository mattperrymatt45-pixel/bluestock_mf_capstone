"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 1: Live NAV Fetch from mfapi.in

Fetches live/historical NAV data from the public mfapi.in REST API
(no authentication required) for HDFC Top 100 plus 5 selected schemes,
and saves each response as a raw CSV under data/raw/live/.

API docs: https://www.mfapi.in/
Endpoint: GET https://api.mfapi.in/mf/{scheme_code}

Usage:
    python scripts/live_nav_fetch.py
"""

from pathlib import Path
import time
import requests
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = PROJECT_ROOT / "data" / "raw" / "live"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://api.mfapi.in/mf/{code}"

# HDFC Top 100 Direct (Task 4) + 5 selected schemes (Task 5)
SCHEMES = {
    "125497": "HDFC_Top_100",
    "119551": "SBI_Bluechip",
    "120503": "ICICI_Bluechip",
    "118632": "Nippon_Large_Cap",
    "119092": "Axis_Bluechip",
    "120841": "Kotak_Bluechip",
}


def fetch_scheme_nav(scheme_code: str, timeout: int = 15) -> dict:
    """Call the mfapi.in endpoint for a single scheme and return parsed JSON."""
    url = BASE_URL.format(code=scheme_code)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.json()


def save_as_csv(payload: dict, scheme_code: str, label: str) -> Path:
    """Convert the mfapi.in JSON payload's NAV data list into a CSV file."""
    meta = payload.get("meta", {})
    nav_data = payload.get("data", [])

    df = pd.DataFrame(nav_data)  # columns: date, nav
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y")
        df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)

    df.insert(0, "amfi_code", scheme_code)
    df.insert(1, "scheme_name", meta.get("scheme_name", label))

    out_path = OUT_DIR / f"{scheme_code}_{label}_nav.csv"
    df.to_csv(out_path, index=False)
    return out_path


def main() -> None:
    print("BLUESTOCK FINTECH - Day 1: Live NAV Fetch (mfapi.in)")
    print(f"Saving results to: {OUT_DIR}\n")

    results = []
    for code, label in SCHEMES.items():
        print(f"Fetching {label} (AMFI code {code}) ...")
        try:
            payload = fetch_scheme_nav(code)
            out_path = save_as_csv(payload, code, label)
            n_rows = len(payload.get("data", []))
            print(f"  OK - {n_rows:,} NAV rows saved -> {out_path}")
            results.append({"amfi_code": code, "label": label, "status": "ok", "rows": n_rows})
        except requests.exceptions.RequestException as exc:
            print(f"  FAILED: {exc}")
            results.append({"amfi_code": code, "label": label, "status": "failed", "error": str(exc)})
        time.sleep(0.5)  # be polite to the free public API

    summary = pd.DataFrame(results)
    print("\nSummary:")
    print(summary.to_string(index=False))

    n_failed = (summary["status"] == "failed").sum()
    if n_failed:
        print(f"\n{n_failed} scheme(s) failed to fetch. Check network access to api.mfapi.in.")
    else:
        print("\nAll schemes fetched successfully.")


if __name__ == "__main__":
    main()
