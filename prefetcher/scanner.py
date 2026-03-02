"""Repo tree scanner — walks a directory tree, respecting exclusions and depth limits."""

from pathlib import Path

EXCLUDED_DIRS = frozenset({
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".eggs",
    "dist",
    "build",
    ".next",
    ".nuxt",
})


def scan_repo_tree(
    repo_path: str | Path,
    max_depth: int = 10,
) -> list[str]:
    """Return a sorted list of relative file paths under *repo_path*.

    Skips directories listed in EXCLUDED_DIRS and stops recursing beyond
    *max_depth* levels (depth 0 = the root directory itself).
    """
    repo_path = Path(repo_path)
    results: list[str] = []
    _walk(repo_path, repo_path, max_depth, 0, results)
    results.sort()
    return results


def _walk(
    root: Path,
    current: Path,
    max_depth: int,
    depth: int,
    acc: list[str],
) -> None:
    if depth > max_depth:
        return
    try:
        entries = sorted(current.iterdir())
    except PermissionError:
        return
    for entry in entries:
        if entry.is_dir():
            if entry.name in EXCLUDED_DIRS:
                continue
            _walk(root, entry, max_depth, depth + 1, acc)
        elif entry.is_file():
            acc.append(str(entry.relative_to(root)))
