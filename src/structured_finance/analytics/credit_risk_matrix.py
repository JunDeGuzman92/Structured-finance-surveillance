"""Generate borrower credit-risk matrix."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/credit_risk_matrix.sql")


def run_report() -> None:
    """Analyze delinquency severity by borrower credit-score band."""

    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    print("AUTO ABS CREDIT RISK MATRIX")
    print("=" * 115)
    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_report()
