#!/bin/bash
set -e

# mise
eval "$(mise activate bash)"
mise fmt
mise install

# Python
uv sync
mise run licenses python --ignore-package tiktoken
# tiktoken declares no License-Expression or license classifier, and its
# License field holds the full MIT text, which exact matching cannot compare.
uv run pip-licenses --packages tiktoken --partial-match --allow-only="MIT License"
uv audit
uv-override-prune --fix
ruff check --fix
ruff format
ty check --error-on-warning
if [[ -n "$CI" ]]; then
  uv run pytest --cov --cov-report=term --cov-report=xml
else
  uv run pytest --cov --cov-report=term
fi

# Shared lint tasks
mise run gha-lint
mise run shell-lint
mise run docker-lint

# Check for uncommitted changes
git diff --exit-code
