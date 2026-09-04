"""Stream-inspect large SEC XML files without loading them fully into memory."""

from collections import Counter
from pathlib import Path

from lxml import etree


MAX_ELEMENTS = 100_000


def strip_namespace(tag) -> str | None:
    """Return a clean XML tag name or None for non-element nodes."""

    if not isinstance(tag, str):
        return None

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def inspect_xml_stream(
    file_path: Path,
    max_elements: int = MAX_ELEMENTS,
) -> None:
    """Inspect the beginning of a large XML file using streaming parsing."""

    print(f"File: {file_path}")
    print(f"File size: {file_path.stat().st_size:,} bytes")
    print(f"Sampling up to: {max_elements:,} XML elements")
    print()

    tag_counts = Counter()
    parent_counts = Counter()
    sample_values = {}

    context = etree.iterparse(
        str(file_path),
        events=("end",),
        recover=True,
        huge_tree=True,
    )

    processed = 0

    for _, element in context:
        tag = strip_namespace(element.tag)

        if tag is None:
            continue

        tag_counts[tag] += 1

        parent = element.getparent()

        if parent is not None:
            parent_tag = strip_namespace(parent.tag)

            if parent_tag is not None:
                parent_counts[parent_tag] += 1

        text = element.text

        if (
            text
            and text.strip()
            and tag not in sample_values
        ):
            sample_values[tag] = text.strip()[:100]

        processed += 1

        # Free memory as we stream.
        element.clear()

        while element.getprevious() is not None:
            del element.getparent()[0]

        if processed >= max_elements:
            break

    print("MOST FREQUENT TAGS")
    print("-" * 60)

    for tag, count in tag_counts.most_common(40):
        print(f"{tag:<45} {count:>10,}")

    print()
    print("MOST FREQUENT PARENT ELEMENTS")
    print("-" * 60)

    for tag, count in parent_counts.most_common(20):
        print(f"{tag:<45} {count:>10,}")

    print()
    print("SAMPLE FIELD VALUES")
    print("-" * 60)

    for tag, value in list(sample_values.items())[:50]:
        print(f"{tag:<40} {value}")


if __name__ == "__main__":
    file_path = Path(
        "data/raw/"
        "exeter_2025_1/"
        "eart2025-1_exhibit102.xml"
    )

    inspect_xml_stream(file_path)