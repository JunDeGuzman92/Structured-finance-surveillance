"""Build a field inventory from SEC EX-102 asset records."""

from collections import Counter, defaultdict
from pathlib import Path
import csv

from lxml import etree


MAX_RECORDS = 5_000

INPUT_FILE = Path(
    "data/raw/"
    "exeter_2025_1/"
    "eart2025-1_exhibit102.xml"
)

OUTPUT_FILE = Path(
    "docs/ex102_field_inventory.csv"
)


def strip_namespace(tag) -> str | None:
    """Return a clean XML tag or None for non-element nodes."""

    if not isinstance(tag, str):
        return None

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def build_field_inventory(
    file_path: Path,
    output_path: Path,
    max_records: int = MAX_RECORDS,
) -> None:
    """Profile field availability across a sample of asset records."""

    presence_count = Counter()
    non_null_count = Counter()
    sample_values = defaultdict(list)

    record_count = 0

    context = etree.iterparse(
        str(file_path),
        events=("end",),
        recover=True,
        huge_tree=True,
    )

    for _, element in context:

        if strip_namespace(element.tag) != "assets":
            continue

        record_count += 1

        fields_seen = set()

        for child in element:

            field_name = strip_namespace(child.tag)

            if field_name is None:
                continue

            fields_seen.add(field_name)

            value = (
                child.text.strip()
                if child.text and child.text.strip()
                else None
            )

            if value is not None:

                non_null_count[field_name] += 1

                if (
                    len(sample_values[field_name]) < 3
                    and value not in sample_values[field_name]
                ):
                    sample_values[field_name].append(value)

        for field_name in fields_seen:
            presence_count[field_name] += 1

        # Release processed XML from memory.
        element.clear()

        parent = element.getparent()

        if parent is not None:
            while element.getprevious() is not None:
                del parent[0]

        if record_count >= max_records:
            break

    all_fields = sorted(presence_count.keys())

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "source_field",
                "records_sampled",
                "field_present_count",
                "non_null_count",
                "presence_pct",
                "non_null_pct",
                "sample_value_1",
                "sample_value_2",
                "sample_value_3",
            ]
        )

        for field_name in all_fields:

            present = presence_count[field_name]
            non_null = non_null_count[field_name]

            samples = sample_values[field_name]

            writer.writerow(
                [
                    field_name,
                    record_count,
                    present,
                    non_null,
                    round(
                        present / record_count * 100,
                        2,
                    ),
                    round(
                        non_null / record_count * 100,
                        2,
                    ),
                    samples[0] if len(samples) > 0 else "",
                    samples[1] if len(samples) > 1 else "",
                    samples[2] if len(samples) > 2 else "",
                ]
            )

    print(f"Records sampled: {record_count:,}")
    print(f"Distinct fields: {len(all_fields):,}")
    print(f"Inventory saved to: {output_path}")

    print()
    print("FIRST 25 FIELDS")
    print("-" * 70)

    for field_name in all_fields[:25]:

        present = presence_count[field_name]
        non_null = non_null_count[field_name]

        print(
            f"{field_name:<45}"
            f" present={present:>5,}"
            f" non_null={non_null:>5,}"
        )


if __name__ == "__main__":
    build_field_inventory(
        INPUT_FILE,
        OUTPUT_FILE,
    )