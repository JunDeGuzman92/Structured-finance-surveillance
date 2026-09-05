"""Diagnose first-payment date parsing between staging and curated layers."""

import duckdb

STAGING_FILE = "data/staging/exeter_2025_1/ex102_assets_full.parquet"

CURATED_FILE = "data/curated/exeter_2025_1/auto_abs_assets_v1.parquet"


def run_diagnostic() -> None:
    """Inspect raw and curated first-payment date values."""

    con = duckdb.connect()

    print("RAW STAGING DATE PROFILE")
    print("=" * 75)

    staging_profile = con.execute(
        f"""
        SELECT
            COUNT(*) AS records,
            COUNT(originalFirstPaymentDate) AS populated_raw_dates,
            COUNT(DISTINCT originalFirstPaymentDate) AS distinct_raw_dates
        FROM read_parquet('{STAGING_FILE}')
        """
    ).fetchdf()

    print(staging_profile.to_string(index=False))

    print()
    print("RAW DATE SAMPLES")
    print("=" * 75)

    raw_samples = con.execute(
        f"""
        SELECT DISTINCT
            originalFirstPaymentDate
        FROM read_parquet('{STAGING_FILE}')
        WHERE originalFirstPaymentDate IS NOT NULL
        LIMIT 20
        """
    ).fetchdf()

    print(raw_samples.to_string(index=False))

    print()
    print("CURATED DATE PROFILE")
    print("=" * 75)

    curated_profile = con.execute(
        f"""
        SELECT
            COUNT(*) AS records,
            COUNT(original_first_payment_date)
                AS successfully_parsed_dates,

            MIN(original_first_payment_date)
                AS earliest_date,

            MAX(original_first_payment_date)
                AS latest_date

        FROM read_parquet('{CURATED_FILE}')
        """
    ).fetchdf()

    print(curated_profile.to_string(index=False))

    con.close()


if __name__ == "__main__":
    run_diagnostic()
