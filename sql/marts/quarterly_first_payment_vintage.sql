WITH base AS (
    SELECT
        asset_id,
        current_balance,
        obligor_credit_score,
        payment_to_income,
        current_delinquency_days,
        original_first_payment_date,

        EXTRACT(
            YEAR FROM original_first_payment_date
        ) AS vintage_year,

        EXTRACT(
            QUARTER FROM original_first_payment_date
        ) AS vintage_quarter,

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

    WHERE original_first_payment_date IS NOT NULL
),

summary AS (
    SELECT
        vintage_year,
        vintage_quarter,

        COUNT(*) AS loan_count,

        SUM(current_balance)
            AS current_balance,

        SUM(
            current_balance * obligor_credit_score
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN obligor_credit_score IS NOT NULL
                    THEN current_balance
                    ELSE 0
                END
            ),
            0
        ) AS weighted_avg_credit_score,

        SUM(
            current_balance * pti_pct
        )
        /
        NULLIF(
            SUM(
                CASE
                    WHEN pti_pct IS NOT NULL
                    THEN current_balance
                    ELSE 0
                END
            ),
            0
        ) AS weighted_avg_pti_pct,

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

    FROM base

    GROUP BY
        vintage_year,
        vintage_quarter
)

SELECT
    vintage_year,

    'Q' || CAST(vintage_quarter AS INTEGER)
        AS vintage_quarter,

    CAST(vintage_year AS VARCHAR)
        || ' Q'
        || CAST(vintage_quarter AS INTEGER)
        AS vintage_label,

    loan_count,

    current_balance,

    ROUND(
        100.0 * current_balance
        / SUM(current_balance) OVER (),
        2
    ) AS pool_balance_share_pct,

    ROUND(
        weighted_avg_credit_score,
        1
    ) AS weighted_avg_credit_score,

    ROUND(
        weighted_avg_pti_pct,
        2
    ) AS weighted_avg_pti_pct,

    ROUND(
        100.0 * balance_30_plus
        / NULLIF(current_balance, 0),
        4
    ) AS delinquency_30_plus_pct,

    ROUND(
        100.0 * balance_60_plus
        / NULLIF(current_balance, 0),
        4
    ) AS delinquency_60_plus_pct,

    ROUND(
        100.0 * balance_90_plus
        / NULLIF(current_balance, 0),
        4
    ) AS delinquency_90_plus_pct

FROM summary

ORDER BY
    vintage_year,
    vintage_quarter;