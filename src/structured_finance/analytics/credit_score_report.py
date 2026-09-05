"""Generate borrower credit-score surveillance analysis."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/credit_score_bands.sql")


def run_report() -> None:
    """Analyze pool exposure and delinquency by credit-score band."""

    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    print("AUTO ABS CREDIT SCORE SURVEILLANCE")
    print("=" * 110)

    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_report()
