#!/bin/bash
set -e

# mise
eval "$(mise activate bash)"
mise install

# Python
uv sync --extra dev
uv run pip-licenses --partial-match --allow-only="Apache;BSD;CNRI-Python;ISC;MIT;MPL;PSF;Python Software Foundation"
uv audit
ruff check --fix
ruff format
ty check
if [[ -n "$CI" ]]; then
  uv run pytest --cov --cov-report=term --cov-report=xml
else
  uv run pytest --cov --cov-report=term
fi

# Dockerfile
hadolint Dockerfile

# GitHub Actions
pinact run
zizmor --fix .github/workflows/
actionlint
ghalint run

# Check for uncommitted changes
git diff --exit-code
