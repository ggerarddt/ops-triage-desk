"""Regression test: example auto-fill buttons and form fields.

Verifies that the triage page's example buttons carry data attributes
that map to real form field IDs.  This catches the common regression
where generated code breaks the one-click example buttons.
"""
import pytest
import re

from core.config import SEED_USERS
from core.database import init_schema, seed_users
from app import app


@pytest.fixture(scope="module")
def test_db_path(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("triage") / "test.db"
    init_schema(str(db_file))
    seed_users(SEED_USERS, str(db_file))
    return str(db_file)


@pytest.fixture(autouse=True)
def patch_db(monkeypatch, test_db_path):
    import core.database as db_mod
    orig_get = db_mod._get_conn
    def patched(path=None):
        return orig_get(test_db_path)
    monkeypatch.setattr(db_mod, "_get_conn", patched)
    return test_db_path


# Form field IDs referenced by static/app.js
FORM_FIELD_IDS = [
    "title",
    "description",
    "business_area",
    "system_affected",
    "impact_level",
    "urgency",
    "customer_impact",
]


class TestExampleButtonRegression:
    """Ensure example buttons are wired correctly to form fields."""

    def _get_triage_page(self):
        """Log in as operator and fetch the triage page."""
        app.secret_key = "test-only"
        with app.test_client() as client:
            client.post("/login", data={
                "username": "operator1",
                "password": "ChangeMe123!",
            })
            resp = client.get("/triage")
            assert resp.status_code == 200
            return resp.data.decode()

    def test_example_buttons_exist(self):
        html = self._get_triage_page()
        buttons = re.findall(r'<button[^>]*class="example-btn"', html)
        assert len(buttons) == 3, f"Expected 3 example buttons, found {len(buttons)}"

    def test_buttons_have_data_attributes(self):
        html = self._get_triage_page()
        buttons = re.findall(r'<button[^>]*class="example-btn"[^>]*>', html)
        required_attrs = [
            "data-title", "data-description", "data-business_area",
            "data-system_affected", "data-impact_level",
            "data-urgency", "data-customer_impact",
        ]
        for i, btn in enumerate(buttons):
            for attr in required_attrs:
                assert attr in btn, (
                    f"Button {i+1} missing attribute '{attr}': {btn[:100]}"
                )

    def test_page_has_all_form_fields(self):
        """Every field that app.js targets must exist in the rendered HTML."""
        html = self._get_triage_page()
        for field_id in FORM_FIELD_IDS:
            assert f'id="{field_id}"' in html or f"id='{field_id}'" in html, (
                f"Form field #{field_id} not found in rendered triage page"
            )

    def test_script_src_references_app_js(self):
        html = self._get_triage_page()
        assert "app.js" in html, "app.js not referenced in triage page"

    def test_data_attribute_values_are_nonempty(self):
        """All data-* values on example buttons should be non-empty strings."""
        html = self._get_triage_page()
        buttons = re.findall(r'<button[^>]*class="example-btn"[^>]*>', html)
        data_attrs = [
            "data-title", "data-description", "data-business_area",
            "data-system_affected", "data-impact_level",
            "data-urgency", "data-customer_impact",
        ]
        for btn in buttons:
            for attr in data_attrs:
                match = re.search(rf'{attr}="([^"]*)"', btn)
                assert match is not None, f"Missing {attr} on button"
                assert match.group(1), f"{attr} is empty on button: {btn[:80]}"
