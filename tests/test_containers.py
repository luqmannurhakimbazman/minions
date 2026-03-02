"""Tests for the agent Dockerfile and entrypoint script."""

from pathlib import Path

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

    def test_dockerfile_installs_nodejs(self):
        content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
        assert "nodejs" in content or "node" in content

    def test_dockerfile_installs_claude_cli(self):
        content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
        assert "@anthropic-ai/claude-code" in content

    def test_dockerfile_installs_github_cli(self):
        content = (CONTAINERS_DIR / "Dockerfile.agent").read_text()
        assert "githubcli" in content or "github-cli" in content


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

    def test_entrypoint_invokes_claude_cli(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "claude" in content
        assert "--print" in content

    def test_entrypoint_skips_permissions(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "--dangerously-skip-permissions" in content

    def test_entrypoint_no_session_persistence(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "--no-session-persistence" in content

    def test_entrypoint_creates_pr(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "gh pr create" in content

    def test_entrypoint_checks_for_commits_before_push(self):
        content = (CONTAINERS_DIR / "entrypoint.sh").read_text()
        assert "git diff" in content or "git rev-list" in content or "git status" in content
