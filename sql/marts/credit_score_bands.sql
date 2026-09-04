WITH classified AS (
    SELECT
        asset_id,
        current_balance,
        obligor_credit_score,
        current_delinquency_days,

        CASE
            WHEN obligor_credit_score IS NULL
                THEN 'Unknown'

            WHEN obligor_credit_score < 500
                THEN '<500'

            WHEN obligor_credit_score BETWEEN 500 AND 549
                THEN '500-549'

            WHEN obligor_credit_score BETWEEN 550 AND 599
                THEN '550-599'

            WHEN obligor_credit_score BETWEEN 600 AND 649
                THEN '600-649'

            WHEN obligor_credit_score BETWEEN 650 AND 699
                THEN '650-699'

            WHEN obligor_credit_score >= 700
                THEN '700+'

            ELSE 'Unknown'
        END AS credit_score_band

    FROM read_parquet(
        'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
    )
),

summary AS (
    SELECT
        credit_score_band,

        COUNT(*) AS loan_count,

        SUM(current_balance)
            AS current_balance,

        AVG(obligor_credit_score)
            AS average_credit_score,

        SUM(
            CASE
                WHEN current_delinquency_days >= 30
                THEN current_balance
                ELSE 0
            END
        ) AS balance_30_plus

    FROM classified

    GROUP BY credit_score_band
)

SELECT
    credit_score_band,

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
    ) AS balance_share_pct,

    ROUND(
        average_credit_score,
        1
    ) AS average_credit_score,

    ROUND(
        100.0 * balance_30_plus
        / NULLIF(current_balance, 0),
        4
    ) AS delinquency_30_plus_pct

FROM summary

ORDER BY
    CASE credit_score_band
        WHEN '<500' THEN 1
        WHEN '500-549' THEN 2
        WHEN '550-599' THEN 3
        WHEN '600-649' THEN 4
        WHEN '650-699' THEN 5
        WHEN '700+' THEN 6
        ELSE 7
    END;