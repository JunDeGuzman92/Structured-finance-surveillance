WITH pool_totals AS (
    SELECT
        COUNT(*) AS asset_count,

        SUM(beginning_loan_balance)
            AS beginning_pool_balance,

        SUM(current_balance)
            AS ending_pool_balance,

        SUM(principal_collected)
            AS principal_collected,

        SUM(charged_off_principal)
            AS charged_off_principal,

        SUM(other_principal_adjustment)
            AS other_principal_adjustments

    FROM read_parquet(
        'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
    )
),

reconciliation AS (
    SELECT
        asset_count,

        beginning_pool_balance,

        ending_pool_balance,

        principal_collected,

        charged_off_principal,

        other_principal_adjustments,

        beginning_pool_balance
            - ending_pool_balance
            AS balance_reduction,

        principal_collected
            + charged_off_principal
            + other_principal_adjustments
            AS principal_movement_total

    FROM pool_totals
)

SELECT
    *,

    balance_reduction
        - principal_movement_total
        AS reconciliation_difference,

    CASE
        WHEN ABS(
            balance_reduction
            - principal_movement_total
        ) < 0.01
        THEN 'PASS'
        ELSE 'FAIL'
    END AS reconciliation_status

FROM reconciliation;