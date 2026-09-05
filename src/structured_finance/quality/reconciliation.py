"""Run the asset-level pool balance roll-forward control."""

from pathlib import Path

import duckdb

SQL_FILE = Path("sql/quality/pool_rollforward_reconciliation.sql")


def money(value) -> str:
    """Format numeric values as currency."""

    if value is None:
        return "N/A"

    return f"${value:,.2f}"


def run_reconciliation() -> None:
    """Execute and report the pool balance reconciliation control."""

    query = SQL_FILE.read_text(encoding="utf-8")

    con = duckdb.connect()

    row = con.execute(query).fetchone()

    (
        asset_count,
        beginning_pool_balance,
        ending_pool_balance,
        principal_collected,
        charged_off_principal,
        other_principal_adjustments,
        balance_reduction,
        principal_movement_total,
        reconciliation_difference,
        reconciliation_status,
    ) = row

    print("POOL BALANCE ROLL-FORWARD CONTROL")
    print("=" * 72)

    print(f"Assets tested:                 {asset_count:,}")

    print()
    print("BALANCES")
    print("-" * 72)

    print(f"Beginning pool balance:       {money(beginning_pool_balance)}")

    print(f"Ending pool balance:          {money(ending_pool_balance)}")

    print()
    print("PRINCIPAL MOVEMENTS")
    print("-" * 72)

    print(f"Principal collected:          {money(principal_collected)}")

    print(f"Charged-off principal:        {money(charged_off_principal)}")

    print(f"Other principal adjustments:  {money(other_principal_adjustments)}")

    print()
    print("CONTROL RESULT")
    print("-" * 72)

    print(f"Beginning - ending:           {money(balance_reduction)}")

    print(f"Principal movement total:     {money(principal_movement_total)}")

    print(f"Difference:                   {money(reconciliation_difference)}")

    print(f"Status:                       {reconciliation_status}")

    con.close()


if __name__ == "__main__":
    run_reconciliation()
