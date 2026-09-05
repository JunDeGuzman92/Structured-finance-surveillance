"""Vintage and seasoning surveillance dashboard."""

import duckdb
import plotly.express as px
import streamlit as st
from shared import (
    PARQUET_FILE,
    parquet_path,
)

DATA_FILE = parquet_path()


st.title("Vintage & Performance Trends")

st.caption(
    "First-payment vintage analysis of Auto ABS collateral, "
    "including exposure, borrower quality, seasoning, and delinquency."
)


@st.cache_data(show_spinner=False)
def load_vintage_data(
    parquet_path_value: str,
    file_modified_time: float,
):
    """Load annual and quarterly vintage surveillance data."""

    _ = file_modified_time

    con = duckdb.connect()

    try:
        headline_query = f"""
            SELECT
                COUNT(*) AS total_loans,

                MIN(original_first_payment_date)
                    AS earliest_first_payment,

                MAX(original_first_payment_date)
                    AS latest_first_payment,

                SUM(
                    CASE
                        WHEN original_first_payment_date
                             > reporting_period
                        THEN 1
                        ELSE 0
                    END
                ) AS future_first_payment_loans

            FROM read_parquet(
                '{parquet_path_value}'
            )
        """

        headline = con.execute(headline_query).fetchdf().iloc[0]

        annual_query = f"""
            WITH base AS (
                SELECT
                    current_balance,
                    obligor_credit_score,
                    current_delinquency_days,
                    remaining_term_months,
                    original_first_payment_date,

                    CAST(
                        EXTRACT(
                            YEAR
                            FROM original_first_payment_date
                        )
                        AS INTEGER
                    ) AS vintage_year,

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
                    '{parquet_path_value}'
                )

                WHERE original_first_payment_date
                    IS NOT NULL
            ),

            summary AS (
                SELECT
                    vintage_year,

                    COUNT(*) AS loan_count,

                    SUM(current_balance)
                        AS current_balance,

                    AVG(months_since_first_payment)
                        AS avg_months_since_first_payment,

                    SUM(
                        current_balance
                        * obligor_credit_score
                    )
                    /
                    NULLIF(
                        SUM(
                            CASE
                                WHEN obligor_credit_score
                                    IS NOT NULL
                                THEN current_balance
                                ELSE 0
                            END
                        ),
                        0
                    ) AS weighted_avg_credit_score,

                    SUM(
                        current_balance
                        * pti_pct
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
                    ) AS balance_90_plus

                FROM base

                GROUP BY vintage_year
            )

            SELECT
                vintage_year,
                loan_count,

                CAST(
                    current_balance
                    AS DOUBLE
                ) AS current_balance,

                CAST(
                    100.0
                    * current_balance
                    / SUM(current_balance) OVER ()
                    AS DOUBLE
                ) AS pool_balance_share_pct,

                CAST(
                    avg_months_since_first_payment
                    AS DOUBLE
                ) AS avg_months_since_first_payment,

                CAST(
                    weighted_avg_credit_score
                    AS DOUBLE
                ) AS weighted_avg_credit_score,

                CAST(
                    weighted_avg_pti_pct
                    AS DOUBLE
                ) AS weighted_avg_pti_pct,

                CAST(
                    avg_remaining_term_months
                    AS DOUBLE
                ) AS avg_remaining_term_months,

                CAST(
                    100.0
                    * balance_30_plus
                    / NULLIF(current_balance, 0)
                    AS DOUBLE
                ) AS delinquency_30_plus_pct,

                CAST(
                    100.0
                    * balance_60_plus
                    / NULLIF(current_balance, 0)
                    AS DOUBLE
                ) AS delinquency_60_plus_pct,

                CAST(
                    100.0
                    * balance_90_plus
                    / NULLIF(current_balance, 0)
                    AS DOUBLE
                ) AS delinquency_90_plus_pct

            FROM summary

            ORDER BY vintage_year
        """

        annual = con.execute(annual_query).fetchdf()

        quarterly_query = f"""
            WITH base AS (
                SELECT
                    current_balance,
                    obligor_credit_score,
                    current_delinquency_days,
                    original_first_payment_date,

                    CAST(
                        EXTRACT(
                            YEAR
                            FROM original_first_payment_date
                        )
                        AS INTEGER
                    ) AS vintage_year,

                    CAST(
                        EXTRACT(
                            QUARTER
                            FROM original_first_payment_date
                        )
                        AS INTEGER
                    ) AS vintage_quarter,

                    CASE
                        WHEN payment_to_income IS NULL
                            THEN NULL

                        WHEN payment_to_income <= 1
                            THEN payment_to_income * 100

                        ELSE payment_to_income
                    END AS pti_pct

                FROM read_parquet(
                    '{parquet_path_value}'
                )

                WHERE original_first_payment_date
                    IS NOT NULL
            ),

            summary AS (
                SELECT
                    vintage_year,
                    vintage_quarter,

                    COUNT(*) AS loan_count,

                    SUM(current_balance)
                        AS current_balance,

                    SUM(
                        current_balance
                        * obligor_credit_score
                    )
                    /
                    NULLIF(
                        SUM(
                            CASE
                                WHEN obligor_credit_score
                                    IS NOT NULL
                                THEN current_balance
                                ELSE 0
                            END
                        ),
                        0
                    ) AS weighted_avg_credit_score,

                    SUM(
                        current_balance
                        * pti_pct
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
                vintage_quarter,

                CAST(vintage_year AS VARCHAR)
                    || ' Q'
                    || CAST(vintage_quarter AS VARCHAR)
                    AS vintage_label,

                loan_count,

                CAST(
                    current_balance
                    AS DOUBLE
                ) AS current_balance,

                CAST(
                    100.0
                    * current_balance
                    / SUM(current_balance) OVER ()
                    AS DOUBLE
                ) AS pool_balance_share_pct,

                CAST(
                    weighted_avg_credit_score
                    AS DOUBLE
                ) AS weighted_avg_credit_score,

                CAST(
                    weighted_avg_pti_pct
                    AS DOUBLE
                ) AS weighted_avg_pti_pct,

                CAST(
                    100.0
                    * balance_30_plus
                    / NULLIF(current_balance, 0)
                    AS DOUBLE
                ) AS delinquency_30_plus_pct,

                CAST(
                    100.0
                    * balance_60_plus
                    / NULLIF(current_balance, 0)
                    AS DOUBLE
                ) AS delinquency_60_plus_pct,

                CAST(
                    100.0
                    * balance_90_plus
                    / NULLIF(current_balance, 0)
                    AS DOUBLE
                ) AS delinquency_90_plus_pct

            FROM summary

            ORDER BY
                vintage_year,
                vintage_quarter
        """

        quarterly = con.execute(quarterly_query).fetchdf()

        return headline, annual, quarterly

    finally:
        con.close()


headline, annual, quarterly = load_vintage_data(
    DATA_FILE,
    PARQUET_FILE.stat().st_mtime,
)


# ---------------------------------------------------------------------
# Headline vintage metrics
# ---------------------------------------------------------------------

columns = st.columns(4)

columns[0].metric(
    "Loans Analyzed",
    f"{int(headline['total_loans']):,}",
)

columns[1].metric(
    "Earliest First-Payment Month",
    str(headline["earliest_first_payment"])[:7],
)

columns[2].metric(
    "Latest First-Payment Month",
    str(headline["latest_first_payment"])[:7],
)

columns[3].metric(
    "Future First-Payment Loans",
    f"{int(headline['future_first_payment_loans']):,}",
)

st.divider()


# ---------------------------------------------------------------------
# Annual vintage
# ---------------------------------------------------------------------

annual_tab, quarterly_tab = st.tabs(
    [
        "Annual Vintage",
        "Quarterly Vintage",
    ]
)


with annual_tab:
    st.subheader("Current Pool Exposure by First-Payment Year")

    annual_exposure = px.bar(
        annual,
        x="vintage_year",
        y="current_balance",
        text="pool_balance_share_pct",
        labels={
            "vintage_year": "First-Payment Year",
            "current_balance": "Current Balance",
        },
    )

    annual_exposure.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )

    annual_exposure.update_layout(
        showlegend=False,
    )

    st.plotly_chart(
        annual_exposure,
        width="stretch",
    )

    st.subheader("Delinquency by Annual Vintage")

    annual_rates = annual[
        [
            "vintage_year",
            "delinquency_30_plus_pct",
            "delinquency_60_plus_pct",
            "delinquency_90_plus_pct",
        ]
    ].melt(
        id_vars="vintage_year",
        var_name="delinquency_measure",
        value_name="rate_pct",
    )

    annual_rates["delinquency_measure"] = annual_rates["delinquency_measure"].replace(
        {
            "delinquency_30_plus_pct": "30+ Days",
            "delinquency_60_plus_pct": "60+ Days",
            "delinquency_90_plus_pct": "90+ Days",
        }
    )

    annual_performance = px.line(
        annual_rates,
        x="vintage_year",
        y="rate_pct",
        color="delinquency_measure",
        markers=True,
        labels={
            "vintage_year": "First-Payment Year",
            "rate_pct": "Balance-Weighted Delinquency (%)",
            "delinquency_measure": "Measure",
        },
    )

    st.plotly_chart(
        annual_performance,
        width="stretch",
    )

    st.subheader("Annual Vintage Detail")

    display_annual = annual.copy()

    display_annual["current_balance"] = display_annual["current_balance"].map(
        lambda value: f"${value:,.2f}"
    )

    for column in [
        "pool_balance_share_pct",
        "weighted_avg_pti_pct",
        "delinquency_30_plus_pct",
        "delinquency_60_plus_pct",
        "delinquency_90_plus_pct",
    ]:
        display_annual[column] = display_annual[column].map(
            lambda value: f"{value:.2f}%"
        )

    st.dataframe(
        display_annual,
        width="stretch",
        hide_index=True,
    )


with quarterly_tab:
    st.subheader("Quarterly Vintage Performance")

    quarterly_rates = quarterly[
        [
            "vintage_label",
            "delinquency_30_plus_pct",
            "delinquency_60_plus_pct",
            "delinquency_90_plus_pct",
        ]
    ].melt(
        id_vars="vintage_label",
        var_name="delinquency_measure",
        value_name="rate_pct",
    )

    quarterly_rates["delinquency_measure"] = quarterly_rates[
        "delinquency_measure"
    ].replace(
        {
            "delinquency_30_plus_pct": "30+ Days",
            "delinquency_60_plus_pct": "60+ Days",
            "delinquency_90_plus_pct": "90+ Days",
        }
    )

    quarterly_performance = px.line(
        quarterly_rates,
        x="vintage_label",
        y="rate_pct",
        color="delinquency_measure",
        markers=True,
        labels={
            "vintage_label": "First-Payment Quarter",
            "rate_pct": "Balance-Weighted Delinquency (%)",
            "delinquency_measure": "Measure",
        },
    )

    quarterly_performance.update_layout(
        xaxis_tickangle=-45,
    )

    st.plotly_chart(
        quarterly_performance,
        width="stretch",
    )

    st.subheader("Quarterly Exposure")

    quarterly_exposure = px.bar(
        quarterly,
        x="vintage_label",
        y="current_balance",
        text="pool_balance_share_pct",
        labels={
            "vintage_label": "First-Payment Quarter",
            "current_balance": "Current Balance",
        },
    )

    quarterly_exposure.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
    )

    quarterly_exposure.update_layout(
        showlegend=False,
        xaxis_tickangle=-45,
    )

    st.plotly_chart(
        quarterly_exposure,
        width="stretch",
    )

    st.subheader("Quarterly Vintage Detail")

    display_quarterly = quarterly.copy()

    display_quarterly["current_balance"] = display_quarterly["current_balance"].map(
        lambda value: f"${value:,.2f}"
    )

    for column in [
        "pool_balance_share_pct",
        "weighted_avg_pti_pct",
        "delinquency_30_plus_pct",
        "delinquency_60_plus_pct",
        "delinquency_90_plus_pct",
    ]:
        display_quarterly[column] = display_quarterly[column].map(
            lambda value: f"{value:.2f}%"
        )

    st.dataframe(
        display_quarterly,
        width="stretch",
        hide_index=True,
    )


st.divider()

st.caption(
    "Vintage is based on the reported first-payment month, "
    "not an inferred exact origination date. Source MM/YYYY "
    "values are normalized to the first day of each month for "
    "date arithmetic and grouping."
)
