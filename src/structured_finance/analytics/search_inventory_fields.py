"""Find exact SEC fields that may support pool reconciliation."""

from pathlib import Path

import pandas as pd


INVENTORY_FILE = Path("docs/ex102_field_inventory.csv")

OUTPUT_FILE = Path(
    "docs/reconciliation_field_candidates.csv"
)


def search_inventory() -> None:
    """Find balance, principal, cutoff, and original-balance fields."""

    df = pd.read_csv(INVENTORY_FILE)

    pattern = (
        "balance|principal|original|beginning|"
        "ending|cutoff|amount"
    )

    matches = df[
        df["source_field"]
        .str.lower()
        .str.contains(pattern, na=False)
    ].copy()

    matches = matches.sort_values(
        by="source_field"
    )

    matches.to_csv(
        OUTPUT_FILE,
        index=False,
    )

    print("RECONCILIATION FIELD SEARCH")
    print("=" * 70)
    print(f"Matching fields: {len(matches):,}")
    print(f"Saved to: {OUTPUT_FILE}")
    print()

    print("SOURCE FIELD NAMES")
    print("-" * 70)

    for field in matches["source_field"]:
        print(field)


if __name__ == "__main__":
    search_inventory()