"""Tests for the agent Dockerfile and entrypoint script."""

from pathlib import Path

import pytest

CONTAINERS_DIR = Path(__file__).resolve().parent.parent / "containers"


class TestDockerfileAgent:
    """Verify containers/Dockerfile.agent exists and has required content."""

    def test_dockerfile_exists(self):
        assert (CONTAINERS_DIR / "Dockerfile.agent").is_file()

    def test_dockerfile_installs_git(self):
        content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
        assert "git" in content

    def test_dockerfile_has_entrypoint(self):
        content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
        assert "ENTRYPOINT" in content

    def test_dockerfile_uses_python_base(self):
        content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
        assert "python:" in content.lower() or "FROM python" in content


class TestEntrypoint:
    """Verify containers/entrypoint.sh exists and has required content."""

    def test_entrypoint_exists(self):
        assert (CONTAINERS_DIR / "entrypoint.sh").is_file()

    def test_entrypoint_has_shebang(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert content.startswith("#!/")

    def test_entrypoint_sets_errexit(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "set -e" in content

    def test_entrypoint_references_repo_url(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "REPO_URL" in content

    def test_entrypoint_references_branch_name(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "BRANCH_NAME" in content
