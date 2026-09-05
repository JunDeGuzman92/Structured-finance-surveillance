SELECT
    COUNT(*) AS total_loans,

    COUNT(payment_to_income)
        AS populated_pti,

    COUNT(*) - COUNT(payment_to_income)
        AS missing_pti,

    MIN(payment_to_income)
        AS minimum_pti,

    QUANTILE_CONT(
        payment_to_income,
        0.25
    ) AS pti_25th_pct,

    MEDIAN(payment_to_income)
        AS median_pti,

    QUANTILE_CONT(
        payment_to_income,
        0.75
    ) AS pti_75th_pct,

    QUANTILE_CONT(
        payment_to_income,
        0.95
    ) AS pti_95th_pct,

    MAX(payment_to_income)
        AS maximum_pti

FROM read_parquet(
    'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
);