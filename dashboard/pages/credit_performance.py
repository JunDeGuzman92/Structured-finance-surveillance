"""Credit-performance surveillance dashboard."""

import duckdb
import plotly.express as px
import streamlit as st
from shared import (
    compact_currency,
    parquet_path,
    percentage,
)

st.title("Credit Performance")

st.caption("Point-in-time delinquency and borrower credit-risk surveillance.")


DATA_FILE = parquet_path()


@st.cache_data(show_spinner=False)
def load_credit_performance():

    con = duckdb.connect()

    try:
        headline = (
            con.execute(
                f"""
            SELECT
                SUM(current_balance) AS pool_balance,

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

            FROM read_parquet('{DATA_FILE}')
            """
            )
            .fetchdf()
            .iloc[0]
        )

        delinquency = con.execute(
            f"""
            WITH classified AS (
                SELECT
                    current_balance,

                    CASE
                        WHEN current_delinquency_days = 0
                            THEN 'Current / 0 Days'

                        WHEN current_delinquency_days BETWEEN 1 AND 29
                            THEN '1-29 Days'

                        WHEN current_delinquency_days BETWEEN 30 AND 59
                            THEN '30-59 Days'

                        WHEN current_delinquency_days BETWEEN 60 AND 89
                            THEN '60-89 Days'

                        WHEN current_delinquency_days >= 90
                            THEN '90+ Days'

                        ELSE 'Unknown'
                    END AS delinquency_bucket,

                    CASE
                        WHEN current_delinquency_days = 0 THEN 1
                        WHEN current_delinquency_days BETWEEN 1 AND 29 THEN 2
                        WHEN current_delinquency_days BETWEEN 30 AND 59 THEN 3
                        WHEN current_delinquency_days BETWEEN 60 AND 89 THEN 4
                        WHEN current_delinquency_days >= 90 THEN 5
                        ELSE 6
                    END AS bucket_order

                FROM read_parquet('{DATA_FILE}')
            )

            SELECT
                delinquency_bucket,
                bucket_order,
                COUNT(*) AS loan_count,
                SUM(current_balance) AS current_balance

            FROM classified

            GROUP BY
                delinquency_bucket,
                bucket_order

            ORDER BY bucket_order
            """
        ).fetchdf()

        score = con.execute(
            f"""
            WITH classified AS (
                SELECT
                    current_balance,
                    current_delinquency_days,

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
                        ELSE '700+'
                    END AS credit_score_band,

                    CASE
                        WHEN obligor_credit_score < 500 THEN 1
                        WHEN obligor_credit_score BETWEEN 500 AND 549 THEN 2
                        WHEN obligor_credit_score BETWEEN 550 AND 599 THEN 3
                        WHEN obligor_credit_score BETWEEN 600 AND 649 THEN 4
                        WHEN obligor_credit_score BETWEEN 650 AND 699 THEN 5
                        WHEN obligor_credit_score >= 700 THEN 6
                        ELSE 7
                    END AS band_order

                FROM read_parquet('{DATA_FILE}')
            )

            SELECT
                credit_score_band,
                band_order,
                COUNT(*) AS loan_count,
                SUM(current_balance) AS current_balance,

                100.0
                * SUM(
                    CASE
                        WHEN current_delinquency_days >= 30
                        THEN current_balance
                        ELSE 0
                    END
                )
                / NULLIF(
                    SUM(current_balance),
                    0
                ) AS delinquency_30_plus_pct

            FROM classified

            GROUP BY
                credit_score_band,
                band_order

            ORDER BY band_order
            """
        ).fetchdf()

        return headline, delinquency, score

    finally:
        con.close()


headline, delinquency, score = load_credit_performance()


# ---------------------------------------------------------
# Headline performance metrics
# ---------------------------------------------------------

pool_balance = float(headline["pool_balance"])

balance_30 = float(headline["balance_30_plus"])
balance_60 = float(headline["balance_60_plus"])
balance_90 = float(headline["balance_90_plus"])


cols = st.columns(4)

cols[0].metric(
    "Pool Balance",
    compact_currency(pool_balance),
)

cols[1].metric(
    "30+ Delinquency",
    percentage(
        100 * balance_30 / pool_balance,
        2,
    ),
)

cols[2].metric(
    "60+ Delinquency",
    percentage(
        100 * balance_60 / pool_balance,
        2,
    ),
)

cols[3].metric(
    "90+ Delinquency",
    percentage(
        100 * balance_90 / pool_balance,
        2,
    ),
)


st.divider()


# ---------------------------------------------------------
# Delinquency distribution
# ---------------------------------------------------------

st.subheader("Delinquency Distribution")

delinquency["balance_share_pct"] = (
    100 * delinquency["current_balance"] / delinquency["current_balance"].sum()
)

fig_delinquency = px.bar(
    delinquency,
    x="delinquency_bucket",
    y="balance_share_pct",
    text="balance_share_pct",
    labels={
        "delinquency_bucket": "",
        "balance_share_pct": "Pool Balance Share (%)",
    },
)

fig_delinquency.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside",
)

fig_delinquency.update_layout(
    showlegend=False,
)

st.plotly_chart(
    fig_delinquency,
    width="stretch",
)


# ---------------------------------------------------------
# Credit score performance
# ---------------------------------------------------------

st.subheader("Credit Performance by Borrower Score")

fig_score = px.bar(
    score,
    x="credit_score_band",
    y="delinquency_30_plus_pct",
    text="delinquency_30_plus_pct",
    labels={
        "credit_score_band": "Credit Score Band",
        "delinquency_30_plus_pct": "30+ Delinquency (%)",
    },
)

fig_score.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside",
)

fig_score.update_layout(
    showlegend=False,
)

st.plotly_chart(
    fig_score,
    width="stretch",
)


# ---------------------------------------------------------
# Exposure table
# ---------------------------------------------------------

st.subheader("Credit Score Exposure")

display_score = score[
    [
        "credit_score_band",
        "loan_count",
        "current_balance",
        "delinquency_30_plus_pct",
    ]
].copy()

display_score["current_balance"] = display_score["current_balance"].map(
    lambda x: f"${x:,.2f}"
)

display_score["delinquency_30_plus_pct"] = display_score["delinquency_30_plus_pct"].map(
    lambda x: f"{x:.2f}%"
)

st.dataframe(
    display_score,
    width="stretch",
    hide_index=True,
)
