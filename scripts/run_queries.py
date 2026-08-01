"""
Bluestock Fintech - Mutual Fund Analytics Platform
Day 2, Task 6: Run and verify all analytical SQL queries.

Parses sql/queries.sql (split on '-- Q<n>:' markers), executes each query
against data/db/bluestock_mf.db, and writes formatted results to
reports/query_results.txt.

Usage:
    python scripts/run_queries.py
"""

from pathlib import Path
import re
import sqlite3
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "db" / "bluestock_mf.db"
QUERIES_PATH = PROJECT_ROOT / "sql" / "queries.sql"
REPORT_PATH = PROJECT_ROOT / "reports" / "query_results.txt"


def parse_queries(sql_text: str) -> list[tuple[str, str]]:
    """Split queries.sql into (label, sql) pairs on '-- Q<n>: ...' headers."""
    pattern = re.compile(r"-- (Q\d+: .+)\n(?:-- -+\n)?", re.MULTILINE)
    matches = list(pattern.finditer(sql_text))
    queries = []
    for i, m in enumerate(matches):
        label = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(sql_text)
        sql = sql_text[start:end].strip()
        # Strip trailing comment-only lines / blank lines
        sql = "\n".join(l for l in sql.splitlines() if not l.strip().startswith("--"))
        queries.append((label, sql.strip().rstrip(";")))
    return queries


def main() -> None:
    print("BLUESTOCK FINTECH - Day 2, Task 6: Running analytical SQL queries")
    conn = sqlite3.connect(DB_PATH)

    queries = parse_queries(QUERIES_PATH.read_text())
    print(f"Found {len(queries)} queries in {QUERIES_PATH.name}\n")

    report_lines = ["BLUESTOCK FINTECH - Day 2 Analytical Query Results", "=" * 78, ""]

    for label, sql in queries:
        print(f"--- {label} ---")
        try:
            df = pd.read_sql_query(sql, conn)
        except Exception as exc:
            print(f"  ERROR: {exc}")
            report_lines.append(f"{label}\n{'-' * 78}\nERROR: {exc}\n")
            continue

        preview = df.head(10)
        print(preview.to_string(index=False))
        print(f"  ({len(df)} row(s) returned)\n")

        report_lines.append(label)
        report_lines.append("-" * 78)
        report_lines.append(preview.to_string(index=False))
        report_lines.append(f"({len(df)} row(s) returned)")
        report_lines.append("")

    conn.close()

    REPORT_PATH.write_text("\n".join(report_lines))
    print(f"All queries executed successfully. Results written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
