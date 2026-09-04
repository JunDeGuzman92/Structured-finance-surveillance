"""Build the curated Auto ABS analytical dataset."""

from pathlib import Path

import duckdb


SQL_FILE = Path(
    "sql/marts/"
    "curated_auto_abs_assets_v1.sql"
)

OUTPUT_FILE = Path(
    "data/curated/"
    "exeter_2025_1/"
    "auto_abs_assets_v1.parquet"
)


def build_curated_dataset() -> None:
    """Transform staging SEC records into typed curated records."""

    query = SQL_FILE.read_text(
        encoding="utf-8"
    ).strip().rstrip(";")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = duckdb.connect()

    copy_query = f"""
        COPY (
            {query}
        )
        TO '{OUTPUT_FILE.as_posix()}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD
        )
    """

    connection.execute(copy_query)

    record_count = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet(
            '{OUTPUT_FILE.as_posix()}'
        )
        """
    ).fetchone()[0]

    connection.close()

    print(f"Curated records: {record_count:,}")
    print(f"Output: {OUTPUT_FILE}")
    print(
        f"File size: "
        f"{OUTPUT_FILE.stat().st_size:,} bytes"
    )


if __name__ == "__main__":
    build_curated_dataset()