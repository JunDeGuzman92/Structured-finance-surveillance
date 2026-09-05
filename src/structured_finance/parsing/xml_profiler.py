"""Inspect XML structure before building production parsers."""

from collections import Counter
from pathlib import Path

from lxml import etree


def strip_namespace(tag) -> str | None:
    """Return an XML tag without its namespace.

    Comments and processing instructions do not have normal string tags,
    so those nodes are ignored.
    """

    if not isinstance(tag, str):
        return None

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def profile_xml(file_path: Path) -> None:
    """Display structural information about an XML document."""

    print(f"File: {file_path}")
    print(f"File size: {file_path.stat().st_size:,} bytes")
    print()

    tree = etree.parse(str(file_path))
    root = tree.getroot()

    print("ROOT INFORMATION")
    print("-" * 50)

    print(f"Raw root tag: {root.tag}")
    print(f"Clean root tag: {strip_namespace(root.tag)}")
    print(f"Direct children: {len(root)}")
    print(f"Root attributes: {len(root.attrib)}")

    print()
    print("NAMESPACES")
    print("-" * 50)

    if root.nsmap:
        for prefix, uri in root.nsmap.items():
            print(f"{prefix or '(default)'}: {uri}")
    else:
        print("No namespaces declared.")

    print()
    print("ROOT ATTRIBUTES")
    print("-" * 50)

    if root.attrib:
        for key, value in root.attrib.items():
            clean_key = strip_namespace(key)

            if clean_key is not None:
                print(f"{clean_key} = {value}")
    else:
        print("No root attributes.")

    print()
    print("ELEMENT COUNTS")
    print("-" * 50)

    tag_counts = Counter()

    for element in root.iter():
        clean_tag = strip_namespace(element.tag)

        # Ignore comments, processing instructions,
        # and other non-element XML nodes.
        if clean_tag is None:
            continue

        tag_counts[clean_tag] += 1

    for tag, count in tag_counts.most_common(25):
        print(f"{tag:<35} {count:>10,}")


if __name__ == "__main__":
    file_path = Path("data/raw/exeter_2025_1/eart2025-1_exhibit103.xml")

    profile_xml(file_path)
