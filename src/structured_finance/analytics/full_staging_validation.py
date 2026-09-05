"""Validate the complete EX-102 staging dataset."""

import duckdb

PARQUET_FILE = "data/staging/exeter_2025_1/ex102_assets_full.parquet"


def validate_full_staging() -> None:
    """Run basic validation against the complete staging pool."""

    con = duckdb.connect()

    result = con.execute(
        f"""
        SELECT
            COUNT(*) AS records,

            COUNT(DISTINCT assetNumber)
                AS unique_assets,

            SUM(
                CASE
                    WHEN assetNumber IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS missing_asset_ids,

            SUM(
                CASE
                    WHEN reportingPeriodActualEndBalanceAmount IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS missing_balances

        FROM read_parquet('{PARQUET_FILE}')
        """
    ).fetchdf()

    print("FULL STAGING VALIDATION")
    print("=" * 72)
    print(result.to_string(index=False))

    con.close()


if __name__ == "__main__":
    validate_full_staging()
