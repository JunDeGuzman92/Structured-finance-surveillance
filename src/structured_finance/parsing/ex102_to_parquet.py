"""Parse selected SEC EX-102 asset records into staging Parquet."""

from pathlib import Path

from lxml import etree
import pyarrow as pa
import pyarrow.parquet as pq
import yaml


INPUT_FILE = Path(
    "data/raw/"
    "exeter_2025_1/"
    "eart2025-1_exhibit102.xml"
)

MAPPING_FILE = Path(
    "config/field_mapping.yaml"
)

OUTPUT_FILE = Path(
    "data/staging/"
    "exeter_2025_1/"
    "ex102_assets_sample.parquet"
)

DEAL_ID = "exeter_2025_1"
REPORTING_PERIOD = "2024-12-31"

MAX_RECORDS = 100


def strip_namespace(tag) -> str | None:
    """Remove XML namespace information from normal element tags."""

    if not isinstance(tag, str):
        return None

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def load_source_fields() -> list[str]:
    """Load selected SEC source fields from the mapping file."""

    with MAPPING_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        mapping = yaml.safe_load(file)

    return list(mapping.keys())


def parse_sample() -> None:
    """Stream the first selected SEC asset records into Parquet."""

    source_fields = load_source_fields()
    selected_fields = set(source_fields)

    rows = []

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
                child.text.strip()
                if child.text and child.text.strip()
                else None
            )

            record[field_name] = value

        rows.append(record)

        element.clear()

        parent = element.getparent()

        if parent is not None:
            while element.getprevious() is not None:
                del parent[0]

        if len(rows) >= MAX_RECORDS:
            break

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    schema = pa.schema(
        [
            ("deal_id", pa.string()),
            ("reporting_period", pa.string()),
        ]
        + [
            (field, pa.string())
            for field in source_fields
        ]
    )

    table = pa.Table.from_pylist(
        rows,
        schema=schema,
    )

    pq.write_table(
        table,
        OUTPUT_FILE,
        compression="snappy",
    )

    print(f"Records written: {len(rows):,}")
    print(f"Columns written: {len(table.column_names):,}")
    print(f"Output: {OUTPUT_FILE}")
    print(f"File size: {OUTPUT_FILE.stat().st_size:,} bytes")


if __name__ == "__main__":
    parse_sample()