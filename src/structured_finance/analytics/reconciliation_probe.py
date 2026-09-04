"""Inspect pool-level balances before formal reconciliation controls."""

import duckdb


PARQUET_FILE = (
    "data/curated/"
    "exeter_2025_1/"
    "auto_abs_assets_v1.parquet"
)


def money(value) -> str:
    """Format a numeric value as currency."""

    if value is None:
        return "N/A"

    return f"${value:,.2f}"


def run_probe() -> None:
    """Summarize pool balances and principal movements."""

    con = duckdb.connect()

    result = con.execute(
        f"""
        SELECT
            COUNT(*) AS asset_count,

            COUNT(beginning_loan_balance)
                AS populated_beginning_balances,

            COUNT(original_loan_amount)
                AS populated_original_amounts,

            SUM(beginning_loan_balance)
                AS beginning_pool_balance,

            SUM(current_balance)
                AS ending_pool_balance,

            SUM(original_loan_amount)
                AS total_original_loan_amount,

            SUM(principal_collected)
                AS principal_collected,

            SUM(charged_off_principal)
                AS charged_off_principal,

            SUM(other_principal_adjustment)
                AS other_principal_adjustments,

            SUM(beginning_loan_balance)
                - SUM(current_balance)
                AS balance_reduction

        FROM read_parquet('{PARQUET_FILE}')
        """
    ).fetchone()

    (
        asset_count,
        populated_beginning,
        populated_original,
        beginning_balance,
        ending_balance,
        original_amount,
        principal_collected,
        charged_off,
        other_adjustments,
        balance_reduction,
    ) = result

    movement_total = (
        principal_collected
        + charged_off
        + other_adjustments
    )

    reconciliation_difference = (
        balance_reduction
        - movement_total
    )

    print("POOL BALANCE ROLL-FORWARD")
    print("=" * 65)

    print(f"Asset count:                  {asset_count:,}")
    print(
        f"Beginning balances populated: {populated_beginning:,}"
    )
    print(
        f"Original amounts populated:   {populated_original:,}"
    )

    print()
    print("BALANCES")
    print("-" * 65)

    print(
        f"Beginning pool balance:       "
        f"{money(beginning_balance)}"
    )

    print(
        f"Ending pool balance:          "
        f"{money(ending_balance)}"
    )

    print(
        f"Original loan amount total:   "
        f"{money(original_amount)}"
    )

    print()
    print("PRINCIPAL MOVEMENTS")
    print("-" * 65)

    print(
        f"Principal collected:          "
        f"{money(principal_collected)}"
    )

    print(
        f"Charged-off principal:        "
        f"{money(charged_off)}"
    )

    print(
        f"Other principal adjustments:  "
        f"{money(other_adjustments)}"
    )

    print()
    print("RECONCILIATION")
    print("-" * 65)

    print(
        f"Beginning - ending:           "
        f"{money(balance_reduction)}"
    )

    print(
        f"Principal movement total:     "
        f"{money(movement_total)}"
    )

    print(
        f"Difference:                   "
        f"{money(reconciliation_difference)}"
    )

    status = (
        "PASS"
        if abs(reconciliation_difference) < 0.01
        else "FAIL"
    )

    print(f"Status:                       {status}")

    con.close()


if __name__ == "__main__":
    run_probe()