"""
Bluestock Fintech - Mutual Fund Analytics Platform
Master Pipeline Runner

Runs the full project pipeline end to end, in dependency order:
  1. Data ingestion       - load and validate all 10 raw CSVs
  2. Data cleaning         - clean all 10 datasets -> data/processed/
  3. Database load         - build the SQLite star schema and load it
  4. SQL query verification - run and verify the 10 analytical queries
  5. Dashboard mockups      - regenerate the 4 dashboard PNG pages

Notebook-based stages (EDA, Performance Analytics, Advanced Analytics) are
intentionally NOT re-run here, since re-executing a full notebook on every
pipeline run is slow and their outputs are already committed to the repo.
To rebuild them, run each explicitly:

    python scripts/build_eda_notebook.py && \\
        jupyter nbconvert --to notebook --execute --inplace notebooks/EDA_Analysis.ipynb
    python scripts/build_performance_notebook.py && \\
        jupyter nbconvert --to notebook --execute --inplace notebooks/Performance_Analytics.ipynb
    python scripts/build_advanced_notebook.py && \\
        jupyter nbconvert --to notebook --execute --inplace notebooks/Advanced_Analytics.ipynb

The live mfapi.in fetch (`live_nav_fetch.py`) is also excluded from the
default pipeline since it requires outbound network access this sandboxed
environment doesn't have; run it separately when network access is
available.

Usage:
    python run_pipeline.py
    python run_pipeline.py --skip-db      # skip the SQLite rebuild
    python run_pipeline.py --only clean   # run a single stage
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

STAGES = [
    ("ingest", "Data ingestion", SCRIPTS_DIR / "data_ingestion.py"),
    ("clean", "Data cleaning", SCRIPTS_DIR / "clean_data.py"),
    ("load_db", "SQLite database load", SCRIPTS_DIR / "load_to_db.py"),
    ("queries", "SQL query verification", SCRIPTS_DIR / "run_queries.py"),
    ("dashboard", "Dashboard page 1", SCRIPTS_DIR / "build_dashboard_page1.py"),
    ("dashboard", "Dashboard page 2", SCRIPTS_DIR / "build_dashboard_page2.py"),
    ("dashboard", "Dashboard page 3", SCRIPTS_DIR / "build_dashboard_page3.py"),
    ("dashboard", "Dashboard page 4", SCRIPTS_DIR / "build_dashboard_page4.py"),
]


def run_stage(label: str, script_path: Path) -> float:
    """Run one pipeline stage as a subprocess and return its elapsed time."""
    print(f"\n{'=' * 70}\n{label}\n{'=' * 70}")
    start = time.time()
    result = subprocess.run([sys.executable, str(script_path)], cwd=PROJECT_ROOT)
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"\nFAILED: {label} (exit code {result.returncode}) after {elapsed:.1f}s", file=sys.stderr)
        sys.exit(result.returncode)
    print(f"\n{label} completed in {elapsed:.1f}s")
    return elapsed


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Bluestock MF Capstone data pipeline.")
    parser.add_argument("--skip-db", action="store_true", help="Skip the SQLite database rebuild")
    parser.add_argument("--only", choices=["ingest", "clean", "load_db", "queries", "dashboard"],
                         help="Run only stages matching this key")
    args = parser.parse_args()

    print("BLUESTOCK FINTECH - Mutual Fund Analytics Platform")
    print("Running the full data pipeline...\n")

    pipeline_start = time.time()
    total_elapsed = 0.0
    stages_run = 0

    for key, label, script_path in STAGES:
        if args.only and key != args.only:
            continue
        if args.skip_db and key in ("load_db", "queries"):
            continue
        total_elapsed += run_stage(label, script_path)
        stages_run += 1

    print(f"\n{'=' * 70}")
    print(f"Pipeline complete: {stages_run} stage(s) run in {time.time() - pipeline_start:.1f}s total.")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
