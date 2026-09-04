"""Discover where important fields sit inside the SEC XML hierarchy."""

from pathlib import Path

from lxml import etree


TARGET_FIELDS = {
    "scheduledInterestAmount",
    "scheduledPrincipalAmount",
    "reportingPeriodActualEndBalanceAmount",
    "reportingPeriodScheduledPaymentAmount",
    "totalActualAmountPaid",
    "actualInterestCollectedAmount",
}


def strip_namespace(tag) -> str | None:
    """Remove an XML namespace from a normal element tag."""

    if not isinstance(tag, str):
        return None

    if "}" in tag:
        return tag.split("}", 1)[1]

    return tag


def element_path(element) -> str:
    """Build a readable ancestor path for an XML element."""

    parts = []

    current = element

    while current is not None:
        tag = strip_namespace(current.tag)

        if tag is not None:
            parts.append(tag)

        current = current.getparent()

    return "/" + "/".join(reversed(parts))


def inspect_record_structure(file_path: Path) -> None:
    """Print the hierarchy of selected SEC asset-level fields."""

    print(f"File: {file_path}")
    print()
    print("SEARCHING FOR SAMPLE FINANCIAL FIELDS")
    print("-" * 70)

    found = set()

    context = etree.iterparse(
        str(file_path),
        events=("end",),
        recover=True,
        huge_tree=True,
    )

    for _, element in context:
        tag = strip_namespace(element.tag)

        if tag in TARGET_FIELDS and tag not in found:

            value = (
                element.text.strip()
                if element.text and element.text.strip()
                else "(empty)"
            )

            parent = element.getparent()

            parent_tag = (
                strip_namespace(parent.tag)
                if parent is not None
                else None
            )

            grandparent = (
                parent.getparent()
                if parent is not None
                else None
            )

            grandparent_tag = (
                strip_namespace(grandparent.tag)
                if grandparent is not None
                else None
            )

            print()
            print(f"Field:       {tag}")
            print(f"Value:       {value}")
            print(f"Parent:      {parent_tag}")
            print(f"Grandparent: {grandparent_tag}")
            print(f"Full path:   {element_path(element)}")

            found.add(tag)

        element.clear()

        while element.getprevious() is not None:
            del element.getparent()[0]

        if found == TARGET_FIELDS:
            break

    print()
    print("-" * 70)
    print(f"Fields found: {len(found)} / {len(TARGET_FIELDS)}")


if __name__ == "__main__":
    file_path = Path(
        "data/raw/"
        "exeter_2025_1/"
        "eart2025-1_exhibit102.xml"
    )

    inspect_record_structure(file_path)