WITH base AS (
    SELECT
        asset_id,
        reporting_period,
        original_first_payment_date,
        current_balance,
        obligor_credit_score,
        payment_to_income,
        current_delinquency_days,
        charged_off_principal,
        remaining_term_months,

        EXTRACT(
            YEAR FROM original_first_payment_date
        ) AS first_payment_year,

        DATE_DIFF(
            'month',
            original_first_payment_date,
            reporting_period
        ) AS months_since_first_payment,

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
        first_payment_year,

        COUNT(*) AS loan_count,

        SUM(current_balance)
            AS current_balance,

        AVG(months_since_first_payment)
            AS avg_months_since_first_payment,

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

        AVG(remaining_term_months)
            AS avg_remaining_term_months,

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
        ) AS balance_90_plus,

        SUM(charged_off_principal)
            AS charged_off_principal

    FROM base

    GROUP BY first_payment_year
)

SELECT
    first_payment_year,

    loan_count,

    current_balance,

    ROUND(
        100.0 * current_balance
        / SUM(current_balance) OVER (),
        2
    ) AS pool_balance_share_pct,

    ROUND(
        avg_months_since_first_payment,
        1
    ) AS avg_months_since_first_payment,

    ROUND(
        weighted_avg_credit_score,
        1
    ) AS weighted_avg_credit_score,

    ROUND(
        weighted_avg_pti_pct,
        2
    ) AS weighted_avg_pti_pct,

    ROUND(
        avg_remaining_term_months,
        1
    ) AS avg_remaining_term_months,

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
    ) AS delinquency_90_plus_pct,

    charged_off_principal

FROM summary

ORDER BY first_payment_year;