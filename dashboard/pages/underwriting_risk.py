"""Underwriting-risk surveillance dashboard."""

import duckdb
import plotly.express as px
import streamlit as st

from shared import (
    PARQUET_FILE,
    compact_currency,
    parquet_path,
    percentage,
)


DATA_FILE = parquet_path()


# ---------------------------------------------------------------------
# Page header
# ---------------------------------------------------------------------

st.title("Underwriting Risk")

st.caption(
    "Borrower credit quality, payment burden, "
    "and observed delinquency by underwriting cohort."
)


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_underwriting_data(
    parquet_path_value: str,
    file_modified_time: float,
):
    """Load underwriting cohort surveillance data."""

    # Used to invalidate cache whenever curated data is rebuilt.
    _ = file_modified_time

    con = duckdb.connect()

    try:

        matrix_query = f"""
            WITH normalized AS (
                SELECT
                    asset_id,
                    current_balance,
                    obligor_credit_score,
                    current_delinquency_days,

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
            ),

            classified AS (
                SELECT
                    *,

                    CASE
                        WHEN obligor_credit_score IS NULL
                            THEN 'Unknown'

                        WHEN obligor_credit_score < 500
                            THEN '<500'

                        WHEN obligor_credit_score BETWEEN 500 AND 549
                            THEN '500-549'

                        WHEN obligor_credit_score BETWEEN 550 AND 599
                            THEN '550-599'

                        WHEN obligor_credit_score BETWEEN 600 AND 649
                            THEN '600-649'

                        WHEN obligor_credit_score BETWEEN 650 AND 699
                            THEN '650-699'

                        WHEN obligor_credit_score >= 700
                            THEN '700+'

                        ELSE 'Unknown'
                    END AS credit_score_band,

                    CASE
                        WHEN pti_pct IS NULL
                            THEN 'Unknown'

                        WHEN pti_pct < 10
                            THEN '<10%'

                        WHEN pti_pct < 15
                            THEN '10-14.99%'

                        WHEN pti_pct < 20
                            THEN '15-19.99%'

                        WHEN pti_pct < 25
                            THEN '20-24.99%'

                        WHEN pti_pct < 30
                            THEN '25-29.99%'

                        ELSE '30%+'
                    END AS pti_band

                FROM normalized
            ),

            summary AS (
                SELECT
                    credit_score_band,
                    pti_band,

                    COUNT(*) AS loan_count,

                    SUM(current_balance)
                        AS cohort_balance,

                    AVG(pti_pct)
                        AS average_pti_pct,

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

                FROM classified

                GROUP BY
                    credit_score_band,
                    pti_band
            )

            SELECT
                credit_score_band,
                pti_band,
                loan_count,

                CAST(
                    cohort_balance
                    AS DOUBLE
                ) AS cohort_balance,

                CAST(
                    average_pti_pct
                    AS DOUBLE
                ) AS average_pti_pct,

                CAST(
                    balance_30_plus
                    AS DOUBLE
                ) AS balance_30_plus,

                CAST(
                    100.0
                    * cohort_balance
                    / SUM(cohort_balance) OVER ()
                    AS DOUBLE
                ) AS pool_balance_share_pct,

                CAST(
                    100.0
                    * balance_30_plus
                    / NULLIF(cohort_balance, 0)
                    AS DOUBLE
                ) AS delinquency_30_plus_pct,

                CAST(
                    100.0
                    * balance_60_plus
                    / NULLIF(cohort_balance, 0)
                    AS DOUBLE
                ) AS delinquency_60_plus_pct,

                CAST(
                    100.0
                    * balance_90_plus
                    / NULLIF(cohort_balance, 0)
                    AS DOUBLE
                ) AS delinquency_90_plus_pct

            FROM summary
        """

        matrix = con.execute(
            matrix_query
        ).fetchdf()


        headline_query = f"""
            SELECT
                COUNT(*) AS total_loans,

                SUM(current_balance)
                    AS total_balance,

                SUM(
                    CASE
                        WHEN obligor_credit_score < 600
                        THEN current_balance
                        ELSE 0
                    END
                ) AS sub_600_balance,

                SUM(
                    CASE
                        WHEN current_delinquency_days >= 30
                        THEN current_balance
                        ELSE 0
                    END
                ) AS total_30_plus_balance,

                100.0
                * SUM(
                    current_balance
                    * obligor_credit_score
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

                100.0
                * SUM(
                    current_balance
                    * payment_to_income
                )
                /
                NULLIF(
                    SUM(
                        CASE
                            WHEN payment_to_income IS NOT NULL
                            THEN current_balance
                            ELSE 0
                        END
                    ),
                    0
                ) AS weighted_avg_pti_pct

            FROM read_parquet(
                '{parquet_path_value}'
            )
        """

        headline = (
            con.execute(headline_query)
            .fetchdf()
            .iloc[0]
        )

        return matrix, headline

    finally:
        con.close()


matrix, headline = load_underwriting_data(
    DATA_FILE,
    PARQUET_FILE.stat().st_mtime,
)


# ---------------------------------------------------------------------
# Executive underwriting KPIs
# ---------------------------------------------------------------------

total_balance = float(
    headline["total_balance"]
)

sub_600_balance = float(
    headline["sub_600_balance"]
)

total_30_plus_balance = float(
    headline["total_30_plus_balance"]
)


kpi_columns = st.columns(4)

kpi_columns[0].metric(
    "Weighted Avg. Credit Score",
    f"{float(headline['weighted_avg_credit_score']):,.0f}",
)

kpi_columns[1].metric(
    "Weighted Avg. PTI",
    percentage(
        headline["weighted_avg_pti_pct"],
        2,
    ),
)

kpi_columns[2].metric(
    "Sub-600 Exposure",
    percentage(
        100
        * sub_600_balance
        / total_balance,
        2,
    ),
)

kpi_columns[3].metric(
    "30+ Delinquent Balance",
    compact_currency(
        total_30_plus_balance
    ),
)


st.divider()


# ---------------------------------------------------------------------
# Materiality control
# ---------------------------------------------------------------------

st.subheader("Credit Score × Payment-to-Income Risk Matrix")

st.caption(
    "Heatmap shows balance-weighted 30+ delinquency. "
    "Use the minimum cohort-size control to suppress "
    "statistically small groups."
)


minimum_cohort_size = st.slider(
    "Minimum loans per cohort",
    min_value=1,
    max_value=500,
    value=100,
    step=25,
)


material_matrix = matrix[
    matrix["loan_count"]
    >= minimum_cohort_size
].copy()


# ---------------------------------------------------------------------
# Heatmap
# ---------------------------------------------------------------------

credit_order = [
    "<500",
    "500-549",
    "550-599",
    "600-649",
    "650-699",
    "700+",
]

pti_order = [
    "<10%",
    "10-14.99%",
    "15-19.99%",
    "20-24.99%",
    "25-29.99%",
    "30%+",
]


heatmap_data = (
    material_matrix
    .pivot(
        index="credit_score_band",
        columns="pti_band",
        values="delinquency_30_plus_pct",
    )
    .reindex(
        index=credit_order,
        columns=pti_order,
    )
)


fig_heatmap = px.imshow(
    heatmap_data,
    text_auto=".2f",
    aspect="auto",
    labels={
        "x": "Payment-to-Income Band",
        "y": "Credit Score Band",
        "color": "30+ Delinquency (%)",
    },
)


fig_heatmap.update_layout(
    margin=dict(
        l=20,
        r=20,
        t=30,
        b=20,
    ),
)


st.plotly_chart(
    fig_heatmap,
    width="stretch",
)


st.caption(
    "Blank cells indicate cohorts below the selected "
    "minimum-loan threshold or cohorts with no observations."
)


# ---------------------------------------------------------------------
# Top risk contributors
# ---------------------------------------------------------------------

st.divider()

st.subheader("Largest Contributors to 30+ Delinquent Exposure")

top_risk = (
    material_matrix[
        material_matrix["balance_30_plus"] > 0
    ]
    .copy()
    .sort_values(
        by="balance_30_plus",
        ascending=False,
    )
    .head(10)
)


top_risk["cohort"] = (
    top_risk["credit_score_band"]
    + " | "
    + top_risk["pti_band"]
)


fig_risk = px.bar(
    top_risk.sort_values(
        "balance_30_plus"
    ),
    x="balance_30_plus",
    y="cohort",
    orientation="h",
    text="balance_30_plus",
    labels={
        "balance_30_plus":
            "30+ Delinquent Balance",
        "cohort":
            "Underwriting Cohort",
    },
)


fig_risk.update_traces(
    texttemplate="$%{text:,.0f}",
    textposition="outside",
)


fig_risk.update_layout(
    showlegend=False,
    margin=dict(
        l=20,
        r=20,
        t=20,
        b=20,
    ),
)


st.plotly_chart(
    fig_risk,
    width="stretch",
)


# ---------------------------------------------------------------------
# Top-risk table
# ---------------------------------------------------------------------

st.subheader("Material Risk Cohorts")


display_risk = top_risk[
    [
        "credit_score_band",
        "pti_band",
        "loan_count",
        "cohort_balance",
        "pool_balance_share_pct",
        "balance_30_plus",
        "delinquency_30_plus_pct",
        "delinquency_60_plus_pct",
        "delinquency_90_plus_pct",
    ]
].copy()


display_risk["cohort_balance"] = (
    display_risk["cohort_balance"]
    .map(
        lambda value:
        f"${value:,.2f}"
    )
)

display_risk["balance_30_plus"] = (
    display_risk["balance_30_plus"]
    .map(
        lambda value:
        f"${value:,.2f}"
    )
)


for column in [
    "pool_balance_share_pct",
    "delinquency_30_plus_pct",
    "delinquency_60_plus_pct",
    "delinquency_90_plus_pct",
]:
    display_risk[column] = (
        display_risk[column]
        .map(
            lambda value:
            f"{value:.2f}%"
        )
    )


st.dataframe(
    display_risk,
    width="stretch",
    hide_index=True,
)


# ---------------------------------------------------------------------
# Methodology
# ---------------------------------------------------------------------

st.divider()

st.caption(
    "Payment-to-income values are normalized from the "
    "source ratio representation to percentages. Risk "
    "contribution is evaluated using dollar exposure rather "
    "than delinquency rate alone, preventing very small "
    "cohorts from dominating the surveillance view."
)