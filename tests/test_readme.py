"""Tests for README.md presence and content."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestReadme:
    def test_readme_exists(self):
        assert (ROOT / "README.md").is_file()

    def test_readme_contains_project_name(self):
        text = (ROOT / "README.md").read_text()
        assert "Minions" in text

    def test_readme_contains_quick_start(self):
        text = (ROOT / "README.md").read_text()
        assert "Quick Start" in text

    def test_readme_contains_architecture(self):
        text = (ROOT / "README.md").read_text()
        assert "Architecture" in text

    def test_readme_contains_docker(self):
        text = (ROOT / "README.md").read_text()
        assert "docker" in text.lower()
