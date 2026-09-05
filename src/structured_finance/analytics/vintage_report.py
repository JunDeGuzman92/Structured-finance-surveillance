"""Analyze Auto ABS performance by first-payment vintage."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/first_payment_vintage.sql")

OUTPUT_FILE = Path("docs/first_payment_vintage.csv")


def run_report() -> None:
    """Generate annual first-payment vintage surveillance."""

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

    print("AUTO ABS FIRST-PAYMENT VINTAGE ANALYSIS")
    print("=" * 125)

    print(
        result[
            [
                "first_payment_year",
                "loan_count",
                "current_balance",
                "pool_balance_share_pct",
                "weighted_avg_credit_score",
                "weighted_avg_pti_pct",
                "delinquency_30_plus_pct",
                "delinquency_60_plus_pct",
            ]
        ].to_string(index=False)
    )

    print()
    print(f"Saved to: {OUTPUT_FILE}")

    con.close()


if __name__ == "__main__":
    run_report()
