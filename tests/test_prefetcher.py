"""Tests for the prefetcher package."""

import subprocess

from prefetcher.collect import prefetch
from prefetcher.git_context import get_recent_commits
from prefetcher.scanner import scan_repo_tree
from prefetcher.search import search_keywords

# ── Task 3.1: Repo tree scanner ──────────────────────────────────────


def test_scan_empty_dir(tmp_path):
    """Scanning an empty directory returns an empty list."""
    result = scan_repo_tree(tmp_path)
    assert result == []


def test_scan_finds_files(tmp_path):
    """Scanner discovers files in nested directories."""
    (tmp_path / "a.py").write_text("print('a')")
    sub = tmp_path / "src"
    sub.mkdir()
    (sub / "b.py").write_text("print('b')")

    result = scan_repo_tree(tmp_path)
    assert "a.py" in result
    assert "src/b.py" in result


def test_scan_respects_depth_limit(tmp_path):
    """Scanner stops recursing beyond max_depth."""
    deep = tmp_path / "l1" / "l2" / "l3"
    deep.mkdir(parents=True)
    (tmp_path / "top.py").write_text("")
    (tmp_path / "l1" / "mid.py").write_text("")
    (deep / "deep.py").write_text("")

    result = scan_repo_tree(tmp_path, max_depth=2)
    assert "top.py" in result
    assert "l1/mid.py" in result
    # l3 is at depth 3, should be excluded
    assert "l1/l2/l3/deep.py" not in result


def test_scan_excludes_hidden_and_venv(tmp_path):
    """Scanner skips .git, .venv, node_modules, __pycache__, etc."""
    (tmp_path / "keep.py").write_text("")
    for excluded in [".git", ".venv", "node_modules", "__pycache__"]:
        d = tmp_path / excluded
        d.mkdir()
        (d / "secret.py").write_text("")

    result = scan_repo_tree(tmp_path)
    assert "keep.py" in result
    for excluded in [".git", ".venv", "node_modules", "__pycache__"]:
        assert f"{excluded}/secret.py" not in result


# ── Task 3.2: Keyword search ─────────────────────────────────────────


def test_search_keywords_finds_matching_files(tmp_path):
    """search_keywords returns files containing the given keywords."""
    (tmp_path / "app.py").write_text("def authenticate(user): pass")
    (tmp_path / "utils.py").write_text("def helper(): pass")

    results = search_keywords(tmp_path, ["authenticate"])
    assert any("app.py" in r for r in results)
    assert not any("utils.py" in r for r in results)


def test_search_keywords_no_results_for_nonsense(tmp_path):
    """search_keywords returns empty list when nothing matches."""
    (tmp_path / "code.py").write_text("print('hello')")

    results = search_keywords(tmp_path, ["xyzzy_bogus_token_999"])
    assert results == []


def test_search_keywords_limits_results(tmp_path):
    """search_keywords respects max_results."""
    for i in range(10):
        (tmp_path / f"file{i}.py").write_text("keyword_match")

    results = search_keywords(tmp_path, ["keyword_match"], max_results=3)
    assert len(results) <= 3


# ── Task 3.2: Git context ────────────────────────────────────────────


def test_get_recent_commits_returns_strings(tmp_path):
    """get_recent_commits returns a list of strings from a real git repo."""
    # Initialize a tiny git repo with one commit
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path,
        capture_output=True,
    )
    (tmp_path / "f.txt").write_text("hi")
    subprocess.run(["git", "add", "."], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=tmp_path,
        capture_output=True,
    )

    commits = get_recent_commits(tmp_path, count=5)
    assert len(commits) == 1
    assert isinstance(commits[0], str)
    assert "init" in commits[0]


def test_get_recent_commits_empty_for_non_git(tmp_path):
    """get_recent_commits returns empty list for a non-git directory."""
    commits = get_recent_commits(tmp_path)
    assert commits == []


# ── Task 3.2: Prefetch orchestrator ──────────────────────────────────


def test_prefetch_returns_expected_keys(tmp_path):
    """prefetch returns a dict with tree, relevant_files, and git_log."""
    (tmp_path / "main.py").write_text("def run(): pass")

    result = prefetch(tmp_path, "run the application")
    assert isinstance(result, dict)
    assert "tree" in result
    assert "relevant_files" in result
    assert "git_log" in result
    assert "main.py" in result["tree"]
