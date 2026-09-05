"""Identify useful structured-finance fields from the EX-102 inventory."""

from pathlib import Path

import pandas as pd

INVENTORY_FILE = Path("docs/ex102_field_inventory.csv")


KEYWORDS = [
    "asset",
    "balance",
    "principal",
    "interest",
    "payment",
    "credit",
    "score",
    "income",
    "employment",
    "geographic",
    "vehicle",
    "manufacturer",
    "model",
    "term",
    "origination",
    "original",
    "delinquen",
    "days",
    "charge",
    "loss",
    "recover",
    "repossess",
    "extension",
    "maturity",
]


def select_candidate_fields() -> None:
    """Print finance-relevant SEC fields from the field inventory."""

    df = pd.read_csv(INVENTORY_FILE)

    pattern = "|".join(KEYWORDS)

    candidates = df[
        df["source_field"].str.lower().str.contains(pattern, na=False)
    ].copy()

    candidates = candidates.sort_values(
        by=[
            "presence_pct",
            "non_null_pct",
            "source_field",
        ],
        ascending=[
            False,
            False,
            True,
        ],
    )

    print(f"Total inventory fields: {len(df):,}")
    print(f"Candidate fields: {len(candidates):,}")
    print()

    print(
        candidates[
            [
                "source_field",
                "presence_pct",
                "non_null_pct",
                "sample_value_1",
            ]
        ].to_string(index=False)
    )


if __name__ == "__main__":
    select_candidate_fields()
