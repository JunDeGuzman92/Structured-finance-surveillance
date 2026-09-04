SELECT
    vehicle_model,
    COUNT(*) AS loan_count,
    SUM(current_balance) AS balance,
    ROUND(
        100.0
        * SUM(current_balance)
        / SUM(SUM(current_balance)) OVER (),
        2
    ) AS balance_share_pct

FROM read_parquet(
    'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
)

GROUP BY vehicle_model

ORDER BY balance DESC
LIMIT 10;