"""Basic SEC EDGAR client utilities."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_ARCHIVES_URL = "https://www.sec.gov/Archives/edgar/data"

SEC_USER_AGENT = os.getenv("SEC_USER_AGENT")

if not SEC_USER_AGENT:
    raise RuntimeError(
        "SEC_USER_AGENT is not configured. "
        "Create a .env file using .env.example as a template."
    )

HEADERS = {
    "User-Agent": SEC_USER_AGENT,
}


def accession_without_dashes(accession_number: str) -> str:
    """Convert an SEC accession number to its archive-directory format."""
    return accession_number.replace("-", "")


def build_filing_url(
    cik: str,
    accession_number: str,
    filename: str,
) -> str:
    """Build the SEC archive URL for a document within a filing."""

    clean_cik = cik.lstrip("0")
    clean_accession = accession_without_dashes(accession_number)

    return f"{BASE_ARCHIVES_URL}/{clean_cik}/{clean_accession}/{filename}"


if __name__ == "__main__":
    url = build_filing_url(
        cik="0002049379",
        accession_number="0000929638-25-000164",
        filename="eart2025-1_exhibit103.xml",
    )

    print(f"SEC URL: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    print(f"HTTP status: {response.status_code}")
    print(f"Content length: {len(response.content):,} bytes")
