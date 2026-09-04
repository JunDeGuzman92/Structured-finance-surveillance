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
            AS total_balance,

        SUM(
            CASE
                WHEN current_delinquency_days >= 30
                THEN current_balance
                ELSE 0
            END
        ) AS balance_30_plus,

        SUM(
            CASE
                WHEN current_delinquency_days >= 60
                THEN current_balance
                ELSE 0
            END
        ) AS balance_60_plus,

        SUM(
            CASE
                WHEN current_delinquency_days >= 90
                THEN current_balance
                ELSE 0
            END
        ) AS balance_90_plus

    FROM classified

    GROUP BY credit_score_band
)

SELECT
    credit_score_band,

    loan_count,

    total_balance,

    ROUND(
        100.0 * total_balance
        / SUM(total_balance) OVER (),
        2
    ) AS pool_balance_share_pct,

    ROUND(
        100.0 * balance_30_plus
        / NULLIF(total_balance, 0),
        4
    ) AS delinquency_30_plus_pct,

    ROUND(
        100.0 * balance_60_plus
        / NULLIF(total_balance, 0),
        4
    ) AS delinquency_60_plus_pct,

    ROUND(
        100.0 * balance_90_plus
        / NULLIF(total_balance, 0),
        4
    ) AS delinquency_90_plus_pct

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