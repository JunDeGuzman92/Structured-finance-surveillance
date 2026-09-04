"""Run stored SQL analytical reports."""

from pathlib import Path

import duckdb


SQL_FILE = Path(
    "sql/marts/vehicle_model_concentration.sql"
)


def run_report() -> None:
    """Execute a stored SQL report."""

    query = SQL_FILE.read_text(
        encoding="utf-8"
    )

    con = duckdb.connect()

    result = con.execute(query).fetchdf()

    print("TOP VEHICLE MODEL CONCENTRATIONS")
    print("=" * 80)
    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_report()