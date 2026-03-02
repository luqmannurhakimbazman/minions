"""Tests for the prefetcher package."""

from prefetcher.scanner import scan_repo_tree


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
