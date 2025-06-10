#!/bin/bash
set -e

pip install -r dev-requirements.txt

if [[ "$1" == "ci" ]]; then
  black --check ./*.py ./app/*.py ./tests/*.py
else
  black ./*.py ./app/*.py ./tests/*.py
fi

flake8 ./*.py ./app/*.py ./tests/*.py
mypy ./*.py ./app/*.py ./tests/*.py

if [[ "$1" == "ci" ]]; then
  pytest --cov=main --cov=app --cov-branch --cov-report=term --cov-report=xml
else
  pytest --cov=main --cov=app --cov-branch --cov-report=term
fi
