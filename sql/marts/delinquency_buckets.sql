WITH classified AS (
    SELECT
        asset_id,
        current_balance,
        current_delinquency_days,

        CASE
            WHEN current_delinquency_days IS NULL
                THEN 'Unknown'

            WHEN current_delinquency_days = 0
                THEN 'Current'

            WHEN current_delinquency_days BETWEEN 1 AND 29
                THEN '1-29 Days'

            WHEN current_delinquency_days BETWEEN 30 AND 59
                THEN '30-59 Days'

            WHEN current_delinquency_days BETWEEN 60 AND 89
                THEN '60-89 Days'

            WHEN current_delinquency_days >= 90
                THEN '90+ Days'

            ELSE 'Unknown'
        END AS delinquency_bucket

    FROM read_parquet(
        'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
    )
),

summary AS (
    SELECT
        delinquency_bucket,

        COUNT(*) AS loan_count,

        SUM(current_balance)
            AS current_balance

    FROM classified

    GROUP BY delinquency_bucket
)

SELECT
    delinquency_bucket,

    loan_count,

    current_balance,

    ROUND(
        100.0 * loan_count
        / SUM(loan_count) OVER (),
        2
    ) AS loan_share_pct,

    ROUND(
        100.0 * current_balance
        / SUM(current_balance) OVER (),
        2
    ) AS balance_share_pct

FROM summary

ORDER BY
    CASE delinquency_bucket
        WHEN 'Current' THEN 1
        WHEN '1-29 Days' THEN 2
        WHEN '30-59 Days' THEN 3
        WHEN '60-89 Days' THEN 4
        WHEN '90+ Days' THEN 5
        ELSE 6
    END;