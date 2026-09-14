#!/bin/bash
set -e

# mise
eval "$(mise activate bash)"
mise fmt
mise install

# Python
uv sync
# Licenses that may ship alongside MIT code: permissive ones, plus MPL-2.0,
# whose terms stay with its own files. Matching is exact, so a license string
# not listed here, including a new SPDX expression, fails for a human to read.
allowed_licenses=(
  # SPDX identifiers
  0BSD
  Apache-2.0
  BlueOak-1.0.0
  BSD-2-Clause
  BSD-3-Clause
  CC0-1.0
  CNRI-Python
  ISC
  MIT
  MIT-0
  MIT-CMU
  MPL-2.0
  PSF-2.0
  Python-2.0
  Zlib
  # Names from license classifiers and free-form License fields
  "Apache License 2.0"
  "Apache Software License"
  "BSD License"
  "ISC License (ISCL)"
  "MIT License"
  "Mozilla Public License 2.0 (MPL 2.0)"
  "Python Software Foundation License"
  # SPDX expressions
  "Apache-2.0 AND CNRI-Python"
  "Apache-2.0 AND MIT"
  "Apache-2.0 OR BSD-2-Clause"
  "Apache-2.0 OR BSD-3-Clause"
  "Apache-2.0 OR MIT"
  "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0"
  "MPL-2.0 AND (Apache-2.0 OR MIT)"
  "MPL-2.0 AND MIT"
)
uv run pip-licenses --ignore-packages tiktoken --allow-only="$(IFS=';' && echo "${allowed_licenses[*]}")"
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
