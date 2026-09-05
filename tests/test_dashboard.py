"""Smoke tests for the Streamlit surveillance dashboard."""

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

APP_FILE = PROJECT_ROOT / "dashboard" / "app.py"

DATA_FILE = (
    PROJECT_ROOT / "data" / "curated" / "exeter_2025_1" / "auto_abs_assets_v1.parquet"
)


pytestmark = pytest.mark.skipif(
    not DATA_FILE.exists(),
    reason="Curated dashboard dataset not available",
)


def test_dashboard_entrypoint_runs():
    """Executive Overview should render without exceptions."""

    app = AppTest.from_file(
        APP_FILE,
        default_timeout=15,
    )

    app.run()

    assert not app.exception


@pytest.mark.parametrize(
    "page",
    [
        "pages/credit_performance.py",
        "pages/underwriting_risk.py",
        "pages/vintage_analysis.py",
        "pages/data_quality.py",
    ],
)
def test_dashboard_pages_run(page):
    """Every registered surveillance page should render."""

    app = AppTest.from_file(
        APP_FILE,
        default_timeout=15,
    )

    app.run()

    app.switch_page(page)
    app.run()

    assert not app.exception
