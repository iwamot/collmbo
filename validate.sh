#!/bin/bash
set -e

# mise
eval "$(mise activate bash)"
mise fmt
mise install

# Python
uv sync --extra dev
uv run pip-licenses --partial-match --allow-only="Apache;BSD;CNRI-Python;ISC;MIT;MPL;PSF;Python Software Foundation"
uv audit
uv run uv-override-prune
ruff check --fix
ruff format
ty check
if [[ -n "$CI" ]]; then
  uv run pytest --cov --cov-report=term --cov-report=xml
else
  uv run pytest --cov --cov-report=term
fi

# Shared lint tasks
mise run gha-lint
mise run docker-lint

# Check for uncommitted changes
git diff --exit-code
