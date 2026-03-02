"""Git context — retrieves recent commit history."""

import subprocess
from pathlib import Path


def get_recent_commits(
    repo_path: str | Path,
    count: int = 20,
) -> list[str]:
    """Return the last *count* one-line commit messages from the git repo at *repo_path*.

    Returns an empty list if *repo_path* is not a git repository or if the
    git command fails for any reason.
    """
    repo_path = Path(repo_path)

    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-n", str(count)],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return []

    if result.returncode != 0:
        return []

    return [line.strip() for line in result.stdout.splitlines() if line.strip()]
