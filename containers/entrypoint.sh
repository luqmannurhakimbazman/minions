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

echo "==> Running task $TASK_ID"
echo "Prompt: $PROMPT"

# Placeholder: the actual agent logic will be injected here
echo "==> Task complete"
