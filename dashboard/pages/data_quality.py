"""Data-quality and financial-control dashboard."""

import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from shared import (
    PARQUET_FILE,
    compact_currency,
    parquet_path,
)


DATA_FILE = parquet_path()


st.title("Data Quality & Controls")

st.caption(
    "Automated completeness, uniqueness, validity, "
    "date-parsing, and financial reconciliation controls."
)


@st.cache_data(show_spinner=False)
def load_quality_data(
    parquet_path_value: str,
    file_modified_time: float,
):
    """Load curated data-quality and reconciliation metrics."""

    _ = file_modified_time

    con = duckdb.connect()

    try:

        query = f"""
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
                ) AS missing_current_balance,

                SUM(
                    CASE
                        WHEN current_balance < 0
                        THEN 1
                        ELSE 0
                    END
                ) AS negative_current_balance,

                COUNT(original_first_payment_date)
                    AS populated_first_payment_date,

                COUNT(obligor_credit_score)
                    AS populated_credit_score,

                COUNT(payment_to_income)
                    AS populated_pti,

                COUNT(original_interest_rate_pct)
                    AS populated_interest_rate,

                COUNT(beginning_loan_balance)
                    AS populated_beginning_balance,

                CAST(
                    SUM(beginning_loan_balance)
                    AS DOUBLE
                ) AS beginning_pool_balance,

                CAST(
                    SUM(current_balance)
                    AS DOUBLE
                ) AS ending_pool_balance,

                CAST(
                    SUM(principal_collected)
                    AS DOUBLE
                ) AS principal_collected,

                CAST(
                    SUM(charged_off_principal)
                    AS DOUBLE
                ) AS charged_off_principal,

                CAST(
                    SUM(other_principal_adjustment)
                    AS DOUBLE
                ) AS other_principal_adjustments,

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
                '{parquet_path_value}'
            )
        """

        return (
            con.execute(query)
            .fetchdf()
            .iloc[0]
        )

    finally:
        con.close()


quality = load_quality_data(
    DATA_FILE,
    PARQUET_FILE.stat().st_mtime,
)


records = int(
    quality["records"]
)

unique_assets = int(
    quality["unique_assets"]
)

missing_ids = int(
    quality["missing_asset_ids"]
)

missing_balances = int(
    quality["missing_current_balance"]
)

negative_balances = int(
    quality["negative_current_balance"]
)

reconciliation_difference = float(
    quality["reconciliation_difference"]
)


# ---------------------------------------------------------------------
# Headline controls
# ---------------------------------------------------------------------

st.subheader("Control Summary")

columns = st.columns(5)

columns[0].metric(
    "Records",
    f"{records:,}",
)

columns[1].metric(
    "Unique Assets",
    f"{unique_assets:,}",
)

columns[2].metric(
    "Missing Asset IDs",
    f"{missing_ids:,}",
)

columns[3].metric(
    "Missing Balances",
    f"{missing_balances:,}",
)

columns[4].metric(
    "Reconciliation Difference",
    f"${reconciliation_difference:,.2f}",
)


if abs(reconciliation_difference) < 0.01:
    st.success(
        "Pool balance roll-forward reconciliation: PASS"
    )
else:
    st.error(
        "Pool balance roll-forward reconciliation: FAIL"
    )


st.divider()


# ---------------------------------------------------------------------
# Control register
# ---------------------------------------------------------------------

st.subheader("Automated Control Register")


controls = pd.DataFrame(
    [
        {
            "Control": "Asset ID completeness",
            "Result": f"{missing_ids:,}",
            "Threshold": "0 missing",
            "Status": (
                "PASS"
                if missing_ids == 0
                else "FAIL"
            ),
        },
        {
            "Control": "Asset ID uniqueness",
            "Result": f"{records - unique_assets:,}",
            "Threshold": "0 duplicates",
            "Status": (
                "PASS"
                if records == unique_assets
                else "FAIL"
            ),
        },
        {
            "Control": "Current balance completeness",
            "Result": f"{missing_balances:,}",
            "Threshold": "0 missing",
            "Status": (
                "PASS"
                if missing_balances == 0
                else "FAIL"
            ),
        },
        {
            "Control": "Negative current balances",
            "Result": f"{negative_balances:,}",
            "Threshold": "0 negative",
            "Status": (
                "PASS"
                if negative_balances == 0
                else "FAIL"
            ),
        },
        {
            "Control": "First-payment date parsing",
            "Result": (
                f"{int(quality['populated_first_payment_date']):,}"
            ),
            "Threshold": f"{records:,} populated",
            "Status": (
                "PASS"
                if int(
                    quality["populated_first_payment_date"]
                ) == records
                else "FAIL"
            ),
        },
        {
            "Control": "Pool balance roll-forward",
            "Result": f"${reconciliation_difference:,.2f}",
            "Threshold": "< $0.01 absolute difference",
            "Status": (
                "PASS"
                if abs(reconciliation_difference) < 0.01
                else "FAIL"
            ),
        },
    ]
)


st.dataframe(
    controls,
    width="stretch",
    hide_index=True,
)


st.divider()


# ---------------------------------------------------------------------
# Field completeness
# ---------------------------------------------------------------------

st.subheader("Curated Field Completeness")


completeness = pd.DataFrame(
    {
        "Field": [
            "Asset ID",
            "Current Balance",
            "Beginning Balance",
            "First-Payment Date",
            "Credit Score",
            "Payment-to-Income",
            "Interest Rate",
        ],
        "Populated": [
            records - missing_ids,
            records - missing_balances,
            int(
                quality[
                    "populated_beginning_balance"
                ]
            ),
            int(
                quality[
                    "populated_first_payment_date"
                ]
            ),
            int(
                quality[
                    "populated_credit_score"
                ]
            ),
            int(
                quality[
                    "populated_pti"
                ]
            ),
            int(
                quality[
                    "populated_interest_rate"
                ]
            ),
        ],
    }
)


completeness["Completeness %"] = (
    100.0
    * completeness["Populated"]
    / records
)


fig_completeness = px.bar(
    completeness,
    x="Field",
    y="Completeness %",
    text="Completeness %",
    labels={
        "Completeness %":
            "Completeness (%)",
    },
)


fig_completeness.update_traces(
    texttemplate="%{text:.2f}%",
    textposition="outside",
)


fig_completeness.update_layout(
    yaxis_range=[
        0,
        105,
    ],
    showlegend=False,
)


st.plotly_chart(
    fig_completeness,
    width="stretch",
)


st.divider()


# ---------------------------------------------------------------------
# Financial reconciliation
# ---------------------------------------------------------------------

st.subheader("Pool Balance Roll-Forward")


beginning_balance = float(
    quality["beginning_pool_balance"]
)

ending_balance = float(
    quality["ending_pool_balance"]
)

principal_collected = float(
    quality["principal_collected"]
)

charged_off = float(
    quality["charged_off_principal"]
)

other_adjustments = float(
    quality["other_principal_adjustments"]
)


recon_columns = st.columns(5)

recon_columns[0].metric(
    "Beginning Balance",
    compact_currency(
        beginning_balance
    ),
)

recon_columns[1].metric(
    "Principal Collected",
    compact_currency(
        principal_collected
    ),
)

recon_columns[2].metric(
    "Charge-Offs",
    compact_currency(
        charged_off
    ),
)

recon_columns[3].metric(
    "Other Adjustments",
    f"${other_adjustments:,.2f}",
)

recon_columns[4].metric(
    "Ending Balance",
    compact_currency(
        ending_balance
    ),
)


waterfall = go.Figure(
    go.Waterfall(
        orientation="v",

        measure=[
            "absolute",
            "relative",
            "relative",
            "relative",
            "total",
        ],

        x=[
            "Beginning Balance",
            "Principal Collected",
            "Charge-Offs",
            "Other Adjustments",
            "Ending Balance",
        ],

        y=[
            beginning_balance,
            -principal_collected,
            -charged_off,
            -other_adjustments,
            0,
        ],

        text=[
            compact_currency(
                beginning_balance
            ),
            f"-{compact_currency(principal_collected)}",
            f"-{compact_currency(charged_off)}",
            f"{-other_adjustments:,.2f}",
            compact_currency(
                ending_balance
            ),
        ],

        connector={
            "line": {
                "width": 1,
            }
        },
    )
)


waterfall.update_layout(
    title="Principal Balance Reconciliation",
    showlegend=False,
)


st.plotly_chart(
    waterfall,
    width="stretch",
)


balance_reduction = (
    beginning_balance
    - ending_balance
)

principal_movement = (
    principal_collected
    + charged_off
    + other_adjustments
)


reconciliation_table = pd.DataFrame(
    {
        "Measure": [
            "Beginning pool balance",
            "Ending pool balance",
            "Beginning - ending",
            "Principal collections",
            "Charged-off principal",
            "Other principal adjustments",
            "Total principal movement",
            "Reconciliation difference",
        ],
        "Amount": [
            beginning_balance,
            ending_balance,
            balance_reduction,
            principal_collected,
            charged_off,
            other_adjustments,
            principal_movement,
            reconciliation_difference,
        ],
    }
)


reconciliation_table["Amount"] = (
    reconciliation_table["Amount"]
    .map(
        lambda value:
        f"${value:,.2f}"
    )
)


st.dataframe(
    reconciliation_table,
    width="stretch",
    hide_index=True,
)


st.divider()

st.caption(
    "The reconciliation control validates that the reduction "
    "from beginning to ending asset balance equals reported "
    "principal collections, charge-offs, and other principal "
    "adjustments within a one-cent tolerance. Completeness "
    "controls are calculated directly from the curated "
    "48,196-record asset-level dataset."
)