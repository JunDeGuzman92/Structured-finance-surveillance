SELECT
    COUNT(*) AS total_loans,

    SUM(
        CASE
            WHEN repossessed_flag
            THEN 1
            ELSE 0
        END
    ) AS repossessed_loans,

    SUM(
        CASE
            WHEN payment_extension_count > 0
            THEN 1
            ELSE 0
        END
    ) AS loans_with_extensions,

    SUM(
        CASE
            WHEN charged_off_principal > 0
            THEN 1
            ELSE 0
        END
    ) AS charged_off_loans,

    SUM(charged_off_principal)
        AS total_charged_off_principal

FROM read_parquet(
    'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
);