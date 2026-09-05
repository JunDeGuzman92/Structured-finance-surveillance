"""Stream the full SEC EX-102 asset pool into staging Parquet."""

from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import yaml
from lxml import etree

INPUT_FILE = Path("data/raw/exeter_2025_1/eart2025-1_exhibit102.xml")

MAPPING_FILE = Path("config/field_mapping.yaml")

OUTPUT_FILE = Path("data/staging/exeter_2025_1/ex102_assets_full.parquet")

DEAL_ID = "exeter_2025_1"
REPORTING_PERIOD = "2024-12-31"

BATCH_SIZE = 5_000


def strip_namespace(tag) -> str | None:
    """Remove namespace information from a normal XML element tag."""

    if not isinstance(tag, str):
        return None

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def load_source_fields() -> list[str]:
    """Load selected SEC source fields from YAML."""

    with MAPPING_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        mapping = yaml.safe_load(file)

    return list(mapping.keys())


def write_batch(
    writer: pq.ParquetWriter,
    rows: list[dict],
    schema: pa.Schema,
) -> None:
    """Write one batch of rows to the Parquet file."""

    if not rows:
        return

    table = pa.Table.from_pylist(
        rows,
        schema=schema,
    )

    writer.write_table(table)


def parse_full_pool() -> None:
    """Stream all SEC asset records into a staging Parquet dataset."""

    source_fields = load_source_fields()
    selected_fields = set(source_fields)

    schema = pa.schema(
        [
            ("deal_id", pa.string()),
            ("reporting_period", pa.string()),
        ]
        + [(field, pa.string()) for field in source_fields]
    )

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Remove an older output so we always rebuild cleanly.
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    rows = []
    record_count = 0

    writer = pq.ParquetWriter(
        OUTPUT_FILE,
        schema=schema,
        compression="zstd",
    )

    try:
        context = etree.iterparse(
            str(INPUT_FILE),
            events=("end",),
            recover=True,
            huge_tree=True,
        )

        for _, element in context:
            if strip_namespace(element.tag) != "assets":
                continue

            record = {
                "deal_id": DEAL_ID,
                "reporting_period": REPORTING_PERIOD,
            }

            for source_field in source_fields:
                record[source_field] = None

            for child in element:
                field_name = strip_namespace(child.tag)

                if field_name not in selected_fields:
                    continue

                value = (
                    child.text.strip() if child.text and child.text.strip() else None
                )

                record[field_name] = value

            rows.append(record)
            record_count += 1

            element.clear()

            parent = element.getparent()

            if parent is not None:
                while element.getprevious() is not None:
                    del parent[0]

            if len(rows) >= BATCH_SIZE:
                write_batch(
                    writer,
                    rows,
                    schema,
                )

                print(f"Processed: {record_count:,} asset records")

                rows.clear()

        # Write the final partial batch.
        write_batch(
            writer,
            rows,
            schema,
        )

    finally:
        writer.close()

    print()
    print("FULL EX-102 PARSE COMPLETE")
    print("=" * 60)
    print(f"Records written: {record_count:,}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"Parquet size: {OUTPUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    parse_full_pool()
