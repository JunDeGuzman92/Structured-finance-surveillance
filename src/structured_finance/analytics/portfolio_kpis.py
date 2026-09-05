"""Calculate initial Auto ABS portfolio surveillance KPIs."""

import duckdb

PARQUET_FILE = "data/curated/exeter_2025_1/auto_abs_assets_v1.parquet"


def calculate_kpis() -> None:
    """Calculate portfolio-level credit and collateral metrics."""

    con = duckdb.connect()

    kpis = con.execute(
        f"""
        SELECT
            COUNT(*) AS loan_count,

            SUM(current_balance)
                AS current_pool_balance,

            AVG(current_balance)
                AS average_loan_balance,

            SUM(
                current_balance
                * original_interest_rate_pct
            )
            /
            NULLIF(
                SUM(current_balance),
                0
            )
                AS weighted_avg_interest_rate_pct,

            AVG(vehicle_value)
                AS average_vehicle_value,

            SUM(charged_off_principal)
                AS charged_off_principal,

            SUM(
                CASE
                    WHEN repossessed_flag
                    THEN 1
                    ELSE 0
                END
            )
                AS repossessed_loans,

            SUM(
                CASE
                    WHEN payment_extension_count > 0
                    THEN 1
                    ELSE 0
                END
            )
                AS loans_with_extensions

        FROM read_parquet('{PARQUET_FILE}')
        """
    ).fetchdf()

    print("AUTO ABS PORTFOLIO KPIs")
    print("=" * 72)
    print(kpis.to_string(index=False))

    con.close()


if __name__ == "__main__":
    calculate_kpis()
