"""Validate the curated Auto ABS analytical dataset."""

import duckdb


PARQUET_FILE = (
    "data/curated/"
    "exeter_2025_1/"
    "auto_abs_assets_v1.parquet"
)


def validate_curated() -> None:
    """Inspect schema and basic quality metrics."""

    con = duckdb.connect()

    print("CURATED SCHEMA")
    print("=" * 72)

    schema = con.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{PARQUET_FILE}')
        """
    ).fetchdf()

    print(
        schema[
            ["column_name", "column_type"]
        ].to_string(index=False)
    )

    print()
    print("BASIC QUALITY CHECKS")
    print("=" * 72)

    checks = con.execute(
        f"""
        SELECT
            COUNT(*) AS records,

            COUNT(DISTINCT asset_id)
                AS unique_assets,

            SUM(
                CASE
                    WHEN asset_id IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS missing_asset_ids,

            SUM(
                CASE
                    WHEN current_balance IS NULL
                    THEN 1
                    ELSE 0
                END
            ) AS missing_balances,

            SUM(
                CASE
                    WHEN current_balance < 0
                    THEN 1
                    ELSE 0
                END
            ) AS negative_balances

        FROM read_parquet('{PARQUET_FILE}')
        """
    ).fetchdf()

    print(checks.to_string(index=False))

    con.close()


if __name__ == "__main__":
    validate_curated()