WITH normalized AS (
    SELECT
        asset_id,
        current_balance,
        obligor_credit_score,
        current_delinquency_days,

        CASE
            WHEN payment_to_income IS NULL
                THEN NULL
            WHEN payment_to_income <= 1
                THEN payment_to_income * 100
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
            ELSE '30%+'
        END AS pti_band

    FROM normalized
),

cohorts AS (
    SELECT
        credit_score_band,
        pti_band,

        COUNT(*) AS loan_count,

        SUM(current_balance)
            AS cohort_balance,

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

    GROUP BY
        credit_score_band,
        pti_band
),

metrics AS (
    SELECT
        credit_score_band,
        pti_band,
        loan_count,
        cohort_balance,
        balance_30_plus,
        balance_60_plus,
        balance_90_plus,

        ROUND(
            100.0 * cohort_balance
            / SUM(cohort_balance) OVER (),
            2
        ) AS pool_share_pct,

        ROUND(
            100.0 * balance_30_plus
            / NULLIF(cohort_balance, 0),
            4
        ) AS delinquency_30_plus_pct,

        ROUND(
            100.0 * balance_60_plus
            / NULLIF(cohort_balance, 0),
            4
        ) AS delinquency_60_plus_pct,

        ROUND(
            100.0 * balance_90_plus
            / NULLIF(cohort_balance, 0),
            4
        ) AS delinquency_90_plus_pct

    FROM cohorts
)

SELECT
    credit_score_band,
    pti_band,
    loan_count,
    cohort_balance,
    pool_share_pct,
    balance_30_plus,
    delinquency_30_plus_pct,
    delinquency_60_plus_pct,
    delinquency_90_plus_pct

FROM metrics

-- Avoid ranking tiny cohorts with unstable percentages.
WHERE loan_count >= 100

ORDER BY
    balance_30_plus DESC,
    delinquency_30_plus_pct DESC

LIMIT 15;