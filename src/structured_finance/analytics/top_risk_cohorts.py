"""Identify borrower cohorts contributing the most delinquent exposure."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/top_risk_cohorts.sql")

OUTPUT_FILE = Path("docs/top_risk_cohorts.csv")


def run_report() -> None:
    """Rank material underwriting cohorts by delinquent exposure."""

    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    result.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("TOP AUTO ABS RISK COHORTS")
    print("=" * 115)

    print(
        result[
            [
                "credit_score_band",
                "pti_band",
                "loan_count",
                "cohort_balance",
                "balance_30_plus",
                "delinquency_30_plus_pct",
            ]
        ].to_string(index=False)
    )

    print()
    print(f"Saved to: {OUTPUT_FILE}")

    con.close()


if __name__ == "__main__":
    run_report()
