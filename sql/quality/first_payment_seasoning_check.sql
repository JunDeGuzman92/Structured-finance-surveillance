SELECT
    COUNT(*) AS total_loans,

    MIN(
        DATE_DIFF(
            'month',
            original_first_payment_date,
            reporting_period
        )
    ) AS minimum_months_since_first_payment,

    MAX(
        DATE_DIFF(
            'month',
            original_first_payment_date,
            reporting_period
        )
    ) AS maximum_months_since_first_payment,

    SUM(
        CASE
            WHEN original_first_payment_date > reporting_period
            THEN 1
            ELSE 0
        END
    ) AS future_first_payment_loans,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN original_first_payment_date > reporting_period
                THEN 1
                ELSE 0
            END
        )
        / COUNT(*),
        2
    ) AS future_first_payment_pct

FROM read_parquet(
    'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
);