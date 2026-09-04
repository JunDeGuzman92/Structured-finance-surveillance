"""Generate headline delinquency surveillance KPIs."""

from pathlib import Path

import duckdb


SQL_FILE = Path(
    "sql/marts/delinquency_kpis.sql"
)


def run_report() -> None:
    """Run pool-level delinquency KPIs."""

    query = SQL_FILE.read_text(
        encoding="utf-8"
    )

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    print("AUTO ABS DELINQUENCY KPIs")
    print("=" * 100)
    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_report()