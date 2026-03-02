"""Keyword search — finds files matching keywords using grep."""

import subprocess
from pathlib import Path


def search_keywords(
    repo_path: str | Path,
    keywords: list[str],
    max_results: int = 20,
) -> list[str]:
    """Return files under *repo_path* whose content matches any of *keywords*.

    Uses ``grep -rl`` for portability.  Returns at most *max_results* paths
    (relative to *repo_path*).
    """
    if not keywords:
        return []

    repo_path = Path(repo_path)
    pattern = r"\|".join(keywords)

    try:
        result = subprocess.run(
            ["grep", "-rl", "--include=*", pattern, "."],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    if result.returncode != 0:
        return []

    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    # Normalise "./foo/bar.py" → "foo/bar.py"
    cleaned = [l.removeprefix("./") for l in lines]
    return cleaned[:max_results]
