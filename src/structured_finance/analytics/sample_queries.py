"""Run initial SQL queries against the EX-102 staging dataset."""

import duckdb

PARQUET_FILE = "data/staging/exeter_2025_1/ex102_assets_sample.parquet"


def run_queries() -> None:
    """Run basic validation queries against the staging Parquet file."""

    connection = duckdb.connect()

    # Query 1: verify the number of parsed loan records.
    loan_count_query = f"""
        SELECT
            COUNT(*) AS loans
        FROM read_parquet('{PARQUET_FILE}')
    """

    loan_count = connection.execute(loan_count_query).fetchdf()

    print("LOAN COUNT")
    print("-" * 60)
    print(loan_count.to_string(index=False))

    print()

    # Query 2: inspect a few real SEC loan records.
    sample_query = f"""
        SELECT
            assetNumber,
            reportingPeriodActualEndBalanceAmount,
            vehicleModelYear,
            vehicleModelName,
            originalInterestRatePercentage
        FROM read_parquet('{PARQUET_FILE}')
        LIMIT 10
    """

    sample = connection.execute(sample_query).fetchdf()

    print("SAMPLE ASSET RECORDS")
    print("-" * 60)
    print(sample.to_string(index=False))

    connection.close()


if __name__ == "__main__":
    run_queries()
