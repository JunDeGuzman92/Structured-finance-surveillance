"""Download SEC filing documents into the raw data layer."""

from hashlib import sha256
from pathlib import Path

import requests

from structured_finance.ingestion.sec_client import (
    HEADERS,
    build_filing_url,
)

RAW_DATA_DIR = Path("data/raw")

CHUNK_SIZE = 1024 * 1024  # 1 MB


def download_sec_document(
    cik: str,
    accession_number: str,
    filename: str,
    deal_id: str,
) -> Path:
    """Download one SEC document using streaming I/O."""

    url = build_filing_url(
        cik=cik,
        accession_number=accession_number,
        filename=filename,
    )

    destination_dir = RAW_DATA_DIR / deal_id
    destination_dir.mkdir(parents=True, exist_ok=True)

    destination_path = destination_dir / filename

    print(f"Source: {url}")
    print(f"Destination: {destination_path}")

    file_hash = sha256()
    downloaded_bytes = 0

    with requests.get(
        url,
        headers=HEADERS,
        timeout=60,
        stream=True,
    ) as response:
        response.raise_for_status()

        with destination_path.open("wb") as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                if not chunk:
                    continue

                file.write(chunk)
                file_hash.update(chunk)
                downloaded_bytes += len(chunk)

    print(f"Downloaded: {downloaded_bytes:,} bytes")
    print(f"SHA-256: {file_hash.hexdigest()}")

    return destination_path


if __name__ == "__main__":
    download_sec_document(
        cik="0002049379",
        accession_number="0000929638-25-000164",
        filename="eart2025-1_exhibit102.xml",
        deal_id="exeter_2025_1",
    )
