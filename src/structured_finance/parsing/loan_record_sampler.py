"""Sample complete asset records from SEC EX-102 data."""

from pathlib import Path

from lxml import etree

SAMPLE_RECORDS = 5


def strip_namespace(tag) -> str | None:
    """Return a clean XML tag or None for non-element nodes."""

    if not isinstance(tag, str):
        return None

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def extract_record(element) -> dict[str, str | None]:
    """Extract fields from one SEC assets element."""

    record = {}

    for child in element:
        tag = strip_namespace(child.tag)

        if tag is None:
            continue

        value = child.text.strip() if child.text and child.text.strip() else None

        record[tag] = value

    return record


def sample_asset_records(
    file_path: Path,
    sample_size: int = SAMPLE_RECORDS,
) -> None:
    """Print the first few complete asset records."""

    print(f"File: {file_path}")
    print(f"Sampling: {sample_size} asset records")
    print()

    context = etree.iterparse(
        str(file_path),
        events=("end",),
        recover=True,
        huge_tree=True,
    )

    record_number = 0

    for _, element in context:
        tag = strip_namespace(element.tag)

        # Based on our structure inspection,
        # one candidate loan record is <assets>.
        if tag != "assets":
            continue

        record_number += 1

        record = extract_record(element)

        print("=" * 80)
        print(f"ASSET RECORD {record_number}")
        print(f"Fields found: {len(record)}")
        print("=" * 80)

        for field, value in record.items():
            print(f"{field:<50} {value}")

        print()

        # Free the completed record from memory.
        element.clear()

        parent = element.getparent()

        if parent is not None:
            while element.getprevious() is not None:
                del parent[0]

        if record_number >= sample_size:
            break

    print("-" * 80)
    print(f"Sampled records: {record_number}")


if __name__ == "__main__":
    file_path = Path("data/raw/exeter_2025_1/eart2025-1_exhibit102.xml")

    sample_asset_records(file_path)
