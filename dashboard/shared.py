"""Shared dashboard configuration and utilities."""

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]

PARQUET_FILE = (
    PROJECT_ROOT / "data" / "curated" / "exeter_2025_1" / "auto_abs_assets_v1.parquet"
)


def get_connection() -> duckdb.DuckDBPyConnection:
    """Return an in-memory DuckDB connection."""

    return duckdb.connect()


def parquet_path() -> str:
    """Return the curated Parquet path in SQL-friendly format."""

    return PARQUET_FILE.as_posix()


def compact_currency(value: float) -> str:
    """Format financial values for dashboard KPI cards."""

    value = float(value)

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:,.3f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:,.2f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:,.1f}K"

    return f"${value:,.2f}"


def percentage(value: float, decimals: int = 2) -> str:
    """Format a percentage."""

    return f"{float(value):,.{decimals}f}%"
