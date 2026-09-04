"""Executive dashboard for the Structured Finance Surveillance Platform."""

from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st


# ---------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PARQUET_FILE = (
    PROJECT_ROOT
    / "data"
    / "curated"
    / "exeter_2025_1"
    / "auto_abs_assets_v1.parquet"
)


# ---------------------------------------------------------------------
# Streamlit page configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Structured Finance Surveillance",
    page_icon="📊",
    layout="wide",
)


# ---------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------

def compact_currency(value: float) -> str:
    """Format large currency values for executive KPI cards."""

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.3f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"

    return f"${value:,.2f}"


def currency(value: float) -> str:
    """Format a value as full currency."""

    return f"${float(value):,.2f}"


def percentage(value: float, decimals: int = 2) -> str:
    """Format a value as a percentage."""

    return f"{float(value):,.{decimals}f}%"


# ---------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_dashboard_data(
    parquet_path: str,
    file_modified_time: float,
):
    """
    Load dashboard datasets from the curated Parquet file.

    file_modified_time is passed deliberately so Streamlit invalidates
    the cache whenever the curated Parquet file is rebuilt.
    """

    # The modification time is used for cache invalidation.
    _ = file_modified_time

    con = duckdb.connect()

    try:

        # -------------------------------------------------------------
        # Executive KPIs
        # -------------------------------------------------------------

        kpi_query = f"""
            SELECT
                COUNT(*) AS asset_count,

                CAST(
                    SUM(current_balance)
                    AS DOUBLE
                ) AS pool_balance,

                CAST(
                    AVG(current_balance)
                    AS DOUBLE
                ) AS average_loan_balance,

                CAST(
                    100.0
                    * SUM(
                        current_balance
                        * original_interest_rate_pct
                    )
                    / NULLIF(
                        SUM(current_balance),
                        0
                    )
                    AS DOUBLE
                ) AS weighted_average_apr_pct,

                CAST(
                    COALESCE(
                        SUM(charged_off_principal),
                        0
                    )
                    AS DOUBLE
                ) AS charged_off_principal,

                CAST(
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
                    )
                    AS DOUBLE
                ) AS delinquency_30_plus_pct,

                CAST(
                    100.0
                    * SUM(
                        CASE
                            WHEN current_delinquency_days >= 60
                            THEN current_balance
                            ELSE 0
                        END
                    )
                    / NULLIF(
                        SUM(current_balance),
                        0
                    )
                    AS DOUBLE
                ) AS delinquency_60_plus_pct,

                CAST(
                    100.0
                    * SUM(
                        CASE
                            WHEN current_delinquency_days >= 90
                            THEN current_balance
                            ELSE 0
                        END
                    )
                    / NULLIF(
                        SUM(current_balance),
                        0
                    )
                    AS DOUBLE
                ) AS delinquency_90_plus_pct

            FROM read_parquet(
                '{parquet_path}'
            )
        """

        kpis = (
            con.execute(kpi_query)
            .fetchdf()
            .iloc[0]
            .to_dict()
        )

        # -------------------------------------------------------------
        # Delinquency distribution
        # -------------------------------------------------------------

        delinquency_query = f"""
            WITH classified AS (
                SELECT
                    current_balance,

                    CASE
                        WHEN current_delinquency_days IS NULL
                            THEN 'Unknown'

                        WHEN current_delinquency_days = 0
                            THEN 'Current / 0 days'

                        WHEN current_delinquency_days
                            BETWEEN 1 AND 29
                            THEN '1-29 Days'

                        WHEN current_delinquency_days
                            BETWEEN 30 AND 59
                            THEN '30-59 Days'

                        WHEN current_delinquency_days
                            BETWEEN 60 AND 89
                            THEN '60-89 Days'

                        WHEN current_delinquency_days >= 90
                            THEN '90+ Days'

                        ELSE 'Unknown'
                    END AS delinquency_bucket,

                    CASE
                        WHEN current_delinquency_days = 0
                            THEN 1

                        WHEN current_delinquency_days
                            BETWEEN 1 AND 29
                            THEN 2

                        WHEN current_delinquency_days
                            BETWEEN 30 AND 59
                            THEN 3

                        WHEN current_delinquency_days
                            BETWEEN 60 AND 89
                            THEN 4

                        WHEN current_delinquency_days >= 90
                            THEN 5

                        ELSE 6
                    END AS bucket_order

                FROM read_parquet(
                    '{parquet_path}'
                )
            ),

            summary AS (
                SELECT
                    delinquency_bucket,
                    bucket_order,

                    COUNT(*) AS loan_count,

                    SUM(current_balance)
                        AS current_balance

                FROM classified

                GROUP BY
                    delinquency_bucket,
                    bucket_order
            )

            SELECT
                delinquency_bucket,
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
                ) AS balance_share_pct

            FROM summary

            ORDER BY bucket_order
        """

        delinquency = con.execute(
            delinquency_query
        ).fetchdf()

        # -------------------------------------------------------------
        # Credit-score exposure
        # -------------------------------------------------------------

        credit_query = f"""
            WITH classified AS (
                SELECT
                    current_balance,

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
                        WHEN obligor_credit_score < 500
                            THEN 1

                        WHEN obligor_credit_score BETWEEN 500 AND 549
                            THEN 2

                        WHEN obligor_credit_score BETWEEN 550 AND 599
                            THEN 3

                        WHEN obligor_credit_score BETWEEN 600 AND 649
                            THEN 4

                        WHEN obligor_credit_score BETWEEN 650 AND 699
                            THEN 5

                        WHEN obligor_credit_score >= 700
                            THEN 6

                        ELSE 7
                    END AS band_order

                FROM read_parquet(
                    '{parquet_path}'
                )
            )

            SELECT
                credit_score_band,

                COUNT(*) AS loan_count,

                CAST(
                    SUM(current_balance)
                    AS DOUBLE
                ) AS current_balance,

                CAST(
                    100.0
                    * SUM(current_balance)
                    / SUM(
                        SUM(current_balance)
                    ) OVER ()
                    AS DOUBLE
                ) AS balance_share_pct

            FROM classified

            GROUP BY
                credit_score_band,
                band_order

            ORDER BY band_order
        """

        credit_scores = con.execute(
            credit_query
        ).fetchdf()

        # -------------------------------------------------------------
        # Data-quality / reconciliation controls
        # -------------------------------------------------------------

        quality_query = f"""
            SELECT
                COUNT(*) AS records,

                COUNT(DISTINCT asset_id)
                    AS unique_assets,

                SUM(
                    CASE
                        WHEN asset_id IS NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS missing_asset_ids,

                SUM(
                    CASE
                        WHEN current_balance IS NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS missing_balances,

                SUM(
                    CASE
                        WHEN current_balance < 0
                        THEN 1
                        ELSE 0
                    END
                ) AS negative_balances,

                CAST(
                    (
                        SUM(beginning_loan_balance)
                        - SUM(current_balance)
                    )
                    -
                    (
                        SUM(principal_collected)
                        + SUM(charged_off_principal)
                        + SUM(other_principal_adjustment)
                    )
                    AS DOUBLE
                ) AS reconciliation_difference

            FROM read_parquet(
                '{parquet_path}'
            )
        """

        quality = (
            con.execute(quality_query)
            .fetchdf()
            .iloc[0]
            .to_dict()
        )

        return (
            kpis,
            delinquency,
            credit_scores,
            quality,
        )

    finally:
        con.close()


# ---------------------------------------------------------------------
# Validate data source
# ---------------------------------------------------------------------

if not PARQUET_FILE.exists():

    st.error(
        "Curated dataset not found. "
        "Build the curated dataset before launching the dashboard."
    )

    st.code(
        "python -m structured_finance.database.build_curated"
    )

    st.stop()


parquet_path = PARQUET_FILE.as_posix()

file_modified_time = PARQUET_FILE.stat().st_mtime


# ---------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------

with st.spinner(
    "Loading structured-finance surveillance data..."
):

    (
        kpis,
        delinquency,
        credit_scores,
        quality,
    ) = load_dashboard_data(
        parquet_path,
        file_modified_time,
    )


# ---------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------

st.title(
    "Structured Finance Data Quality & Surveillance Platform"
)

st.caption(
    "Auto ABS • Exeter 2025-1 • SEC ABS-EE / EX-102 "
    "asset-level surveillance"
)

st.divider()


# ---------------------------------------------------------------------
# Executive KPI row
# ---------------------------------------------------------------------

st.subheader("Executive Overview")

row_one = st.columns(4)

row_one[0].metric(
    "Assets",
    f"{int(kpis['asset_count']):,}",
)

row_one[1].metric(
    "Current Pool Balance",
    compact_currency(
        kpis["pool_balance"]
    ),
)

row_one[2].metric(
    "Weighted Avg. APR",
    percentage(
        kpis["weighted_average_apr_pct"],
        2,
    ),
)

row_one[3].metric(
    "Average Loan Balance",
    compact_currency(
        kpis["average_loan_balance"]
    ),
)


row_two = st.columns(4)

row_two[0].metric(
    "30+ Delinquency",
    percentage(
        kpis["delinquency_30_plus_pct"],
        2,
    ),
)

row_two[1].metric(
    "60+ Delinquency",
    percentage(
        kpis["delinquency_60_plus_pct"],
        2,
    ),
)

row_two[2].metric(
    "90+ Delinquency",
    percentage(
        kpis["delinquency_90_plus_pct"],
        2,
    ),
)

row_two[3].metric(
    "Charged-Off Principal",
    compact_currency(
        kpis["charged_off_principal"]
    ),
)

st.divider()


# ---------------------------------------------------------------------
# Reconciliation / data quality
# ---------------------------------------------------------------------

st.subheader("Data Quality & Control Status")

reconciliation_difference = float(
    quality["reconciliation_difference"]
)

reconciliation_passed = (
    abs(reconciliation_difference) < 0.01
)

quality_columns = st.columns(5)

quality_columns[0].metric(
    "Unique Assets",
    f"{int(quality['unique_assets']):,}",
)

quality_columns[1].metric(
    "Missing Asset IDs",
    f"{int(quality['missing_asset_ids']):,}",
)

quality_columns[2].metric(
    "Missing Balances",
    f"{int(quality['missing_balances']):,}",
)

quality_columns[3].metric(
    "Negative Balances",
    f"{int(quality['negative_balances']):,}",
)

quality_columns[4].metric(
    "Reconciliation Difference",
    currency(
        reconciliation_difference
    ),
)


if reconciliation_passed:

    st.success(
        "Pool balance roll-forward reconciliation: PASS"
    )

else:

    st.error(
        "Pool balance roll-forward reconciliation: FAIL"
    )


# ---------------------------------------------------------------------
# Main visualizations
# ---------------------------------------------------------------------

st.divider()

chart_left, chart_right = st.columns(2)


with chart_left:

    st.subheader(
        "Delinquency Distribution"
    )

    delinquency_chart = px.bar(
        delinquency,
        x="delinquency_bucket",
        y="balance_share_pct",
        text="balance_share_pct",
        labels={
            "delinquency_bucket": "",
            "balance_share_pct":
                "Pool Balance Share (%)",
        },
    )

    delinquency_chart.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    delinquency_chart.update_layout(
        showlegend=False,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
    )

    st.plotly_chart(
        delinquency_chart,
        width="stretch",
    )


with chart_right:

    st.subheader(
        "Credit Score Exposure"
    )

    credit_chart = px.pie(
        credit_scores,
        names="credit_score_band",
        values="current_balance",
        hole=0.55,
    )

    credit_chart.update_traces(
        textinfo="percent+label",
    )

    credit_chart.update_layout(
        legend_title_text=(
            "Credit Score Band"
        ),
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
    )

    st.plotly_chart(
        credit_chart,
        width="stretch",
    )


# ---------------------------------------------------------------------
# Detail tables
# ---------------------------------------------------------------------

st.divider()

with st.expander(
    "View delinquency detail"
):

    display_delinquency = delinquency.copy()

    display_delinquency[
        "current_balance"
    ] = display_delinquency[
        "current_balance"
    ].map(
        lambda value: f"${value:,.2f}"
    )

    display_delinquency[
        "balance_share_pct"
    ] = display_delinquency[
        "balance_share_pct"
    ].map(
        lambda value: f"{value:.2f}%"
    )

    st.dataframe(
        display_delinquency,
        width="stretch",
        hide_index=True,
    )


with st.expander(
    "View credit-score detail"
):

    display_credit = credit_scores.copy()

    display_credit[
        "current_balance"
    ] = display_credit[
        "current_balance"
    ].map(
        lambda value: f"${value:,.2f}"
    )

    display_credit[
        "balance_share_pct"
    ] = display_credit[
        "balance_share_pct"
    ].map(
        lambda value: f"{value:.2f}%"
    )

    st.dataframe(
        display_credit,
        width="stretch",
        hide_index=True,
    )


# ---------------------------------------------------------------------
# Methodology note
# ---------------------------------------------------------------------

st.divider()

st.caption(
    "Dashboard metrics are calculated directly from the curated "
    "asset-level Parquet dataset using DuckDB. Delinquency metrics "
    "are point-in-time balance-weighted measures. The reconciliation "
    "control compares beginning-to-ending principal movement against "
    "principal collections, charge-offs, and other principal "
    "adjustments."
)