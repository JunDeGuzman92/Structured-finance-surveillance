"""Analyze borrower underwriting risk by credit score and PTI."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/underwriting_risk_matrix.sql")


def run_report() -> None:
    """Generate credit-score × PTI × delinquency analysis."""

    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    print("AUTO ABS UNDERWRITING RISK MATRIX")
    print("=" * 125)

    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_report()
