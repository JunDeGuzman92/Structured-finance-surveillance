"""Validate first-payment seasoning assumptions."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/quality/first_payment_seasoning_check.sql")


def run_check() -> None:
    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()
    result = con.execute(query).fetchdf()

    print("FIRST-PAYMENT SEASONING CHECK")
    print("=" * 85)
    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_check()
