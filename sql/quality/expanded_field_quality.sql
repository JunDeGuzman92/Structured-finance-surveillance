SELECT
    COUNT(*) AS records,

    COUNT(original_loan_term)
        AS populated_original_term,

    COUNT(remaining_term_months)
        AS populated_remaining_term,

    COUNT(obligor_credit_score)
        AS populated_credit_score,

    COUNT(payment_to_income)
        AS populated_payment_to_income,

    COUNT(current_delinquency_days)
        AS populated_delinquency,

    COUNT(principal_collected)
        AS populated_principal_collected,

    MIN(obligor_credit_score)
        AS min_credit_score,

    MAX(obligor_credit_score)
        AS max_credit_score,

    MIN(current_delinquency_days)
        AS min_delinquency_days,

    MAX(current_delinquency_days)
        AS max_delinquency_days

FROM read_parquet(
    'data/curated/exeter_2025_1/auto_abs_assets_v1.parquet'
);