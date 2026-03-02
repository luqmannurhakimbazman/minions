# Claude CLI Agent Integration Design

**Date:** 2026-03-02
**Approach:** Minimal shell integration (Approach 1)

## Context

The Minions agent container (`containers/Dockerfile.agent` and `containers/entrypoint.sh`) currently has a placeholder where the actual agent logic should run. This design integrates Claude CLI as the agent backend.

## Decisions

- **Auth:** Mount `~/.claude` read-only from host (OAuth/email login)
- **Invocation:** Pipe combined prompt via stdin to `claude --print`
- **Output:** Commit + push + create GitHub PR automatically
- **GitHub auth:** Mount `~/.gitconfig` and `~/.config/gh` read-only from host

## Changes

### 1. Dockerfile.agent

Add `nodejs`, `npm`, Claude CLI (`@anthropic-ai/claude-code`), and GitHub CLI (`gh`) to the image.

### 2. entrypoint.sh

Replace the placeholder with:
1. Clone repo and create branch (existing)
2. Write context file (existing)
3. Build combined prompt from `$PROMPT` + context file reference
4. Pipe to `claude --print --dangerously-skip-permissions --no-session-persistence`
5. Conditionally push branch and create PR via `gh pr create` (only if commits exist)
6. PR dedup: check `gh pr list --head $BRANCH_NAME` before creating

### 3. container_manager.py

Add volume mounts when spawning agent containers:
- `~/.claude` -> `/root/.claude` (ro) — Claude CLI auth
- `~/.config/gh` -> `/root/.config/gh` (ro) — GitHub CLI auth
- `~/.gitconfig` -> `/root/.gitconfig` (ro) — Git config

Mounts are conditional — only added if the path exists on the host.

### 4. No changes needed

- `config.py` — no new settings required
- `docker-compose.yml` — mounts are programmatic in container_manager, not compose
- `pipeline.py` — existing retry logic handles CLI failures

## Error Handling

| Scenario | Handling |
|---|---|
| Claude CLI auth expired | Non-zero exit -> existing retry logic (up to 3x) -> FAILED |
| No changes made by Claude | `git rev-list` check skips push/PR, exit 0 -> COMPLETED |
| PR already exists for branch | `gh pr list --head` check skips duplicate creation |
| Auth mount paths missing on host | Conditional volume mounts — only mount if path exists |
| Large CONTEXT_FILE env var | Acceptable for now (prefetcher filters to relevant files). Future: mount as volume |
