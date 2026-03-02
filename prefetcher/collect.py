"""Prefetch orchestrator — gathers repo context before spawning an agent."""

from pathlib import Path

from prefetcher.scanner import scan_repo_tree
from prefetcher.search import search_keywords
from prefetcher.git_context import get_recent_commits

# Common English stop words to filter out of task descriptions.
_STOP_WORDS = frozenset({
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "it", "as", "be", "was", "were",
    "been", "are", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "have", "has", "had", "not", "no", "so", "if",
    "then", "that", "this", "these", "those", "i", "me", "my", "we", "our",
    "you", "your", "he", "she", "they", "them", "its", "all", "each",
    "every", "any", "some", "such", "just", "about", "up", "out", "into",
})


def _extract_keywords(description: str) -> list[str]:
    """Split *description* into words, dropping stop words and short tokens."""
    words = description.lower().split()
    return [w for w in words if w not in _STOP_WORDS and len(w) > 2]


def prefetch(
    repo_path: str | Path,
    description: str,
) -> dict:
    """Gather context about a repository before spawning an agent container.

    Returns a dict with:
      - **tree**: list of relative file paths in the repo
      - **relevant_files**: files whose content matches keywords from *description*
      - **git_log**: recent one-line commit messages
    """
    repo_path = Path(repo_path)

    tree = scan_repo_tree(repo_path)
    keywords = _extract_keywords(description)
    relevant_files = search_keywords(repo_path, keywords) if keywords else []
    git_log = get_recent_commits(repo_path)

    return {
        "tree": tree,
        "relevant_files": relevant_files,
        "git_log": git_log,
    }
