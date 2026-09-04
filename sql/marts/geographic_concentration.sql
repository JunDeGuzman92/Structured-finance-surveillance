SELECT
    obligor_geography,

    COUNT(*) AS loan_count,

    SUM(current_balance) AS current_balance,

    ROUND(
        100.0
        * SUM(current_balance)
        / SUM(SUM(current_balance)) OVER (),
        2
    ) AS balance_share_pct

FROM read_parquet(
    'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
)

WHERE obligor_geography IS NOT NULL

GROUP BY obligor_geography

ORDER BY current_balance DESC

LIMIT 15;