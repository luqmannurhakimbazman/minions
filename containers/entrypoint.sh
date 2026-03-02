#!/usr/bin/env bash
set -e

echo "==> Cloning repository: $REPO_URL"
git clone --depth=1 "$REPO_URL" repo
cd repo

echo "==> Creating branch: $BRANCH_NAME"
git checkout -b "$BRANCH_NAME"

echo "==> Writing context file"
if [ -n "$CONTEXT_FILE" ]; then
    echo "$CONTEXT_FILE" > /tmp/context.json
fi

echo "==> Running task $TASK_ID with Claude CLI"

FULL_PROMPT="$(cat <<EOF
Task: $PROMPT

Repository context (relevant files, tree, and recent git log) is available at /tmp/context.json.
You are working on branch $BRANCH_NAME in a cloned repository.
Make the necessary code changes to complete the task.
Commit your changes when done.
EOF
)"

echo "$FULL_PROMPT" | claude --print \
    --dangerously-skip-permissions \
    --no-session-persistence

echo "==> Checking for changes"
if ! git diff --quiet HEAD origin/HEAD 2>/dev/null; then
    echo "==> Pushing branch: $BRANCH_NAME"
    git push -u origin "$BRANCH_NAME"

    echo "==> Creating pull request"
    EXISTING_PR=$(gh pr list --head "$BRANCH_NAME" --json number --jq '.[0].number' 2>/dev/null || echo "")
    if [ -z "$EXISTING_PR" ]; then
        gh pr create \
            --title "[minions] $PROMPT" \
            --body "Automated PR created by Minions agent for task \`$TASK_ID\`."
    else
        echo "==> PR #$EXISTING_PR already exists for branch $BRANCH_NAME, skipping"
    fi
else
    echo "==> No changes detected, skipping push and PR"
fi

echo "==> Task complete"
