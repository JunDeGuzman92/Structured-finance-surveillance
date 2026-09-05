"""Profile payment-to-income values before defining risk bands."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/payment_to_income_profile.sql")


def run_report() -> None:
    """Inspect payment-to-income coverage and distribution."""

    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    print("PAYMENT-TO-INCOME PROFILE")
    print("=" * 100)
    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_report()
