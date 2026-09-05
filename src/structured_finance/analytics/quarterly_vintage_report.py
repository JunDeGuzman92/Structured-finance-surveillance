"""Generate quarterly first-payment vintage surveillance."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/marts/quarterly_first_payment_vintage.sql")

OUTPUT_FILE = Path("docs/quarterly_first_payment_vintage.csv")


def run_report() -> None:
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

    print("AUTO ABS QUARTERLY FIRST-PAYMENT VINTAGE")
    print("=" * 120)

    print(
        result[
            [
                "vintage_label",
                "loan_count",
                "current_balance",
                "pool_balance_share_pct",
                "weighted_avg_credit_score",
                "weighted_avg_pti_pct",
                "delinquency_30_plus_pct",
                "delinquency_60_plus_pct",
                "delinquency_90_plus_pct",
            ]
        ].to_string(index=False)
    )

    print()
    print(f"Saved to: {OUTPUT_FILE}")

    con.close()


if __name__ == "__main__":
    run_report()
