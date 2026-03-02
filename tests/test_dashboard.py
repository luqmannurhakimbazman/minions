"""Tests for the Streamlit dashboard."""

import ast
import pathlib

DASHBOARD_PATH = pathlib.Path(__file__).resolve().parent.parent / "dashboard" / "app.py"


class TestDashboardStructure:
    def test_file_exists(self):
        assert DASHBOARD_PATH.exists(), f"{DASHBOARD_PATH} does not exist"

    def test_valid_python(self):
        source = DASHBOARD_PATH.read_text()
        tree = ast.parse(source)
        assert isinstance(tree, ast.Module)

    def test_imports_streamlit(self):
        source = DASHBOARD_PATH.read_text()
        assert "import streamlit" in source or "from streamlit" in source

    def test_imports_httpx(self):
        source = DASHBOARD_PATH.read_text()
        assert "import httpx" in source or "from httpx" in source

    def test_has_page_config(self):
        source = DASHBOARD_PATH.read_text()
        assert "set_page_config" in source

    def test_has_task_form(self):
        source = DASHBOARD_PATH.read_text()
        assert "form" in source.lower()

    def test_has_cancel_functionality(self):
        source = DASHBOARD_PATH.read_text()
        assert "cancel" in source.lower()
