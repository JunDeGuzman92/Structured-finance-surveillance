SELECT
    deal_id,

    CAST(reporting_period AS DATE)
        AS reporting_period,

    assetNumber
        AS asset_id,

    obligorCreditScoreType
        AS credit_score_type,

    obligorEmploymentVerificationCode
        AS employment_verification_code,

    obligorGeographicLocation
        AS obligor_geography,

    obligorIncomeVerificationLevelCode
        AS income_verification_code,

    CAST(
        TRY_STRPTIME(
            originalFirstPaymentDate,
            '%m-%d-%Y'
        ) AS DATE
    ) AS original_first_payment_date,

    TRY_CAST(
        originalInterestRatePercentage
        AS DECIMAL(10,6)
    ) AS original_interest_rate_pct,

    vehicleModelName
        AS vehicle_model,

    TRY_CAST(
        vehicleModelYear
        AS INTEGER
    ) AS vehicle_model_year,

    vehicleNewUsedCode
        AS vehicle_new_used_code,

    vehicleTypeCode
        AS vehicle_type_code,

    TRY_CAST(
        vehicleValueAmount
        AS DECIMAL(18,2)
    ) AS vehicle_value,

    vehicleValueSourceCode
        AS vehicle_value_source_code,

    TRY_CAST(
        reportingPeriodActualEndBalanceAmount
        AS DECIMAL(18,2)
    ) AS current_balance,

    TRY_CAST(
        reportingPeriodScheduledPaymentAmount
        AS DECIMAL(18,2)
    ) AS scheduled_payment,

    TRY_CAST(
        scheduledPrincipalAmount
        AS DECIMAL(18,2)
    ) AS scheduled_principal,

    TRY_CAST(
        scheduledInterestAmount
        AS DECIMAL(18,2)
    ) AS scheduled_interest,

    TRY_CAST(
        totalActualAmountPaid
        AS DECIMAL(18,2)
    ) AS actual_payment,

    TRY_CAST(
        actualInterestCollectedAmount
        AS DECIMAL(18,2)
    ) AS interest_collected,

    CAST(
        TRY_STRPTIME(
            interestPaidThroughDate,
            '%m-%d-%Y'
        ) AS DATE
    ) AS interest_paid_through_date,

    TRY_CAST(
        otherPrincipalAdjustmentAmount
        AS DECIMAL(18,2)
    ) AS other_principal_adjustment,

    TRY_CAST(
        paymentExtendedNumber
        AS INTEGER
    ) AS payment_extension_count,

    TRY_CAST(
        chargedoffPrincipalAmount
        AS DECIMAL(18,2)
    ) AS charged_off_principal,

    TRY_CAST(
        repossessedIndicator
        AS BOOLEAN
    ) AS repossessed_flag,

    TRY_CAST(
        assetSubjectDemandIndicator
        AS BOOLEAN
    ) AS subject_to_demand_flag

    TRY_CAST(
        originalLoanTerm
        AS INTEGER
    ) AS original_loan_term,

    TRY_CAST(
        remainingTermToMaturityNumber
        AS INTEGER
    ) AS remaining_term_months,

    TRY_CAST(
        obligorCreditScore
        AS INTEGER
    ) AS obligor_credit_score,

    TRY_CAST(
        paymentToIncomePercentage
        AS DECIMAL(10,6)
    ) AS payment_to_income,

    TRY_CAST(
        currentDelinquencyStatus
        AS INTEGER
    ) AS current_delinquency_days,

    TRY_CAST(
        actualPrincipalCollectedAmount
        AS DECIMAL(18,2)
    ) AS principal_collected

FROM read_parquet(
    'data/staging/exeter_2025_1/ex102_assets_full.parquet'
);