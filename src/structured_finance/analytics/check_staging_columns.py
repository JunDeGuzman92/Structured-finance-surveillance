"""Check whether proposed fields exist in the full staging dataset."""

import duckdb

PARQUET_FILE = "data/staging/exeter_2025_1/ex102_assets_full.parquet"


PROPOSED_FIELDS = [
    "reportingPeriodBeginningLoanBalanceAmount",
    "originalLoanAmount",
    "originalLoanTerm",
    "remainingTermToMaturityNumber",
    "obligorCreditScore",
    "paymentToIncomePercentage",
    "currentDelinquencyStatus",
    "actualPrincipalCollectedAmount",
    "vehicleManufacturerName",
]


def check_columns() -> None:
    con = duckdb.connect()

    schema = con.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{PARQUET_FILE}')
        """
    ).fetchdf()

    available_fields = set(schema["column_name"].astype(str))

    print("PROPOSED FIELD CHECK")
    print("=" * 75)

    for field in PROPOSED_FIELDS:
        status = "FOUND" if field in available_fields else "NOT FOUND"

        print(f"{field:<50} {status}")

    con.close()


if __name__ == "__main__":
    check_columns()
