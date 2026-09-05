WITH normalized AS (
    SELECT
        asset_id,
        current_balance,
        obligor_credit_score,
        current_delinquency_days,

        CASE
            WHEN payment_to_income IS NULL
                THEN NULL

            -- Handle ratio-style values such as 0.18 = 18%.
            WHEN payment_to_income <= 1
                THEN payment_to_income * 100

            -- Otherwise assume source is already percentage-scaled.
            ELSE payment_to_income
        END AS pti_pct

    FROM read_parquet(
        'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
    )
),

classified AS (
    SELECT
        *,

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
        END AS credit_score_band,

        CASE
            WHEN pti_pct IS NULL
                THEN 'Unknown'
            WHEN pti_pct < 10
                THEN '<10%'
            WHEN pti_pct < 15
                THEN '10-14.99%'
            WHEN pti_pct < 20
                THEN '15-19.99%'
            WHEN pti_pct < 25
                THEN '20-24.99%'
            WHEN pti_pct < 30
                THEN '25-29.99%'
            WHEN pti_pct >= 30
                THEN '30%+'
            ELSE 'Unknown'
        END AS pti_band

    FROM normalized
),

summary AS (
    SELECT
        credit_score_band,
        pti_band,

        COUNT(*) AS loan_count,

        SUM(current_balance)
            AS current_balance,

        AVG(pti_pct)
            AS average_pti_pct,

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
        ) AS balance_60_plus

    FROM classified

    GROUP BY
        credit_score_band,
        pti_band
)

SELECT
    credit_score_band,
    pti_band,

    loan_count,

    current_balance,

    ROUND(
        average_pti_pct,
        2
    ) AS average_pti_pct,

    ROUND(
        100.0
        * current_balance
        / SUM(current_balance) OVER (),
        2
    ) AS pool_balance_share_pct,

    ROUND(
        100.0
        * balance_30_plus
        / NULLIF(current_balance, 0),
        4
    ) AS delinquency_30_plus_pct,

    ROUND(
        100.0
        * balance_60_plus
        / NULLIF(current_balance, 0),
        4
    ) AS delinquency_60_plus_pct

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
    END,

    CASE pti_band
        WHEN '<10%' THEN 1
        WHEN '10-14.99%' THEN 2
        WHEN '15-19.99%' THEN 3
        WHEN '20-24.99%' THEN 4
        WHEN '25-29.99%' THEN 5
        WHEN '30%+' THEN 6
        ELSE 7
    END;