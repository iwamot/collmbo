#!/bin/bash
set -e

# mise
eval "$(mise activate bash)"
mise fmt
mise install

# Python
uv sync --extra dev
uv run pip-licenses --partial-match --allow-only="Apache;BSD;CNRI-Python;ISC;MIT;MPL;PSF;Python Software Foundation"
# PYSEC-2025-183: no fixed version is available for pyjwt.
uv run pip-audit --ignore-vuln PYSEC-2025-183
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
