"""Regression tests for the curated Auto ABS dataset."""

from pathlib import Path

import duckdb
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_FILE = (
    PROJECT_ROOT / "data" / "curated" / "exeter_2025_1" / "auto_abs_assets_v1.parquet"
)

EXPECTED_RECORDS = 48_196


@pytest.fixture(scope="module")
def connection():
    """Provide DuckDB connection for dataset tests."""

    if not DATA_FILE.exists():
        pytest.skip(f"Curated dataset not available: {DATA_FILE}")

    con = duckdb.connect()

    yield con

    con.close()


def query_value(connection, expression: str):
    """Return a single scalar query result."""

    result = connection.execute(
        f"""
        SELECT {expression}
        FROM read_parquet('{DATA_FILE.as_posix()}')
        """
    ).fetchone()

    return result[0]


def test_expected_record_count(connection):
    """The Exeter 2025-1 dataset should contain 48,196 assets."""

    assert (
        query_value(
            connection,
            "COUNT(*)",
        )
        == EXPECTED_RECORDS
    )


def test_asset_ids_are_unique(connection):
    """Each asset should have one unique identifier."""

    records = query_value(
        connection,
        "COUNT(*)",
    )

    unique_assets = query_value(
        connection,
        "COUNT(DISTINCT asset_id)",
    )

    assert unique_assets == records


def test_no_missing_asset_ids(connection):
    """Asset identifiers are mandatory."""

    missing = query_value(
        connection,
        """
        SUM(
            CASE
                WHEN asset_id IS NULL THEN 1
                ELSE 0
            END
        )
        """,
    )

    assert missing == 0


def test_no_missing_current_balances(connection):
    """Current balance should be populated for every asset."""

    missing = query_value(
        connection,
        """
        SUM(
            CASE
                WHEN current_balance IS NULL THEN 1
                ELSE 0
            END
        )
        """,
    )

    assert missing == 0


def test_no_negative_current_balances(connection):
    """Current loan balance should not be negative."""

    negative = query_value(
        connection,
        """
        SUM(
            CASE
                WHEN current_balance < 0 THEN 1
                ELSE 0
            END
        )
        """,
    )

    assert negative == 0


def test_first_payment_dates_are_parsed(connection):
    """Every source first-payment month should parse successfully."""

    populated = query_value(
        connection,
        "COUNT(original_first_payment_date)",
    )

    assert populated == EXPECTED_RECORDS


def test_pool_rollforward_reconciles(connection):
    """Beginning-to-ending principal movement should reconcile."""

    difference = query_value(
        connection,
        """
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
        """,
    )

    assert abs(float(difference)) < 0.01


def test_delinquency_severity_is_monotonic(connection):
    """90+ exposure cannot exceed 60+, which cannot exceed 30+."""

    result = connection.execute(
        f"""
        SELECT
            SUM(
                CASE
                    WHEN current_delinquency_days >= 30
                    THEN current_balance
                    ELSE 0
                END
            ) AS balance_30,

            SUM(
                CASE
                    WHEN current_delinquency_days >= 60
                    THEN current_balance
                    ELSE 0
                END
            ) AS balance_60,

            SUM(
                CASE
                    WHEN current_delinquency_days >= 90
                    THEN current_balance
                    ELSE 0
                END
            ) AS balance_90

        FROM read_parquet(
            '{DATA_FILE.as_posix()}'
        )
        """
    ).fetchone()

    balance_30, balance_60, balance_90 = result

    assert balance_90 <= balance_60 <= balance_30
