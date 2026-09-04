"""Validate curated field mappings against the discovered SEC field inventory."""

from pathlib import Path

import pandas as pd
import yaml


INVENTORY_FILE = Path("docs/ex102_field_inventory.csv")
MAPPING_FILE = Path("config/field_mapping.yaml")


def validate_mapping() -> None:
    """Check that mapped source fields actually exist in SEC EX-102."""

    inventory = pd.read_csv(INVENTORY_FILE)

    inventory_fields = set(
        inventory["source_field"].dropna().astype(str)
    )

    with MAPPING_FILE.open(
        "r",
        encoding="utf-8",
    ) as file:
        mapping = yaml.safe_load(file)

    mapped_fields = set(mapping.keys())

    missing_fields = sorted(
        mapped_fields - inventory_fields
    )

    incomplete_fields = []

    for source_field, config in mapping.items():

        required_keys = {
            "curated_name",
            "data_type",
            "category",
        }

        if not required_keys.issubset(config):
            incomplete_fields.append(source_field)

    print(f"Inventory fields: {len(inventory_fields):,}")
    print(f"Mapped fields:    {len(mapped_fields):,}")
    print()

    if missing_fields:
        print("FIELDS NOT FOUND IN INVENTORY")
        print("-" * 60)

        for field in missing_fields:
            print(field)

    if incomplete_fields:
        print()
        print("INCOMPLETE MAPPING DEFINITIONS")
        print("-" * 60)

        for field in incomplete_fields:
            print(field)

    if not missing_fields and not incomplete_fields:
        print("Mapping validation PASSED")
        print("All mapped SEC fields exist in the inventory.")


if __name__ == "__main__":
    validate_mapping()