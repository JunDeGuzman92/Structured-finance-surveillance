SELECT
    COUNT(*) AS total_loans,

    SUM(current_balance)
        AS total_pool_balance,

    -- 30+ delinquency
    SUM(
        CASE
            WHEN current_delinquency_days >= 30
            THEN 1
            ELSE 0
        END
    ) AS loans_30_plus,

    SUM(
        CASE
            WHEN current_delinquency_days >= 30
            THEN current_balance
            ELSE 0
        END
    ) AS balance_30_plus,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN current_delinquency_days >= 30
                THEN current_balance
                ELSE 0
            END
        )
        / NULLIF(SUM(current_balance), 0),
        4
    ) AS balance_30_plus_pct,

    -- 60+ delinquency
    SUM(
        CASE
            WHEN current_delinquency_days >= 60
            THEN 1
            ELSE 0
        END
    ) AS loans_60_plus,

    SUM(
        CASE
            WHEN current_delinquency_days >= 60
            THEN current_balance
            ELSE 0
        END
    ) AS balance_60_plus,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN current_delinquency_days >= 60
                THEN current_balance
                ELSE 0
            END
        )
        / NULLIF(SUM(current_balance), 0),
        4
    ) AS balance_60_plus_pct,

    -- 90+ delinquency
    SUM(
        CASE
            WHEN current_delinquency_days >= 90
            THEN 1
            ELSE 0
        END
    ) AS loans_90_plus,

    SUM(
        CASE
            WHEN current_delinquency_days >= 90
            THEN current_balance
            ELSE 0
        END
    ) AS balance_90_plus,

    ROUND(
        100.0 *
        SUM(
            CASE
                WHEN current_delinquency_days >= 90
                THEN current_balance
                ELSE 0
            END
        )
        / NULLIF(SUM(current_balance), 0),
        4
    ) AS balance_90_plus_pct

FROM read_parquet(
    'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
);