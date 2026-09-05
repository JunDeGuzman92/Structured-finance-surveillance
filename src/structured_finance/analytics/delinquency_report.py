"""Generate the Auto ABS delinquency surveillance report."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/delinquency_buckets.sql")


def run_report() -> None:
    """Run delinquency analysis on the curated asset pool."""

    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    print("AUTO ABS DELINQUENCY SURVEILLANCE")
    print("=" * 90)
    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_report()
