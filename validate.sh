#!/bin/bash
pip install -r slim-requirements.txt
pip install black && black ./*.py ./app/*.py ./tests/*.py
pip install pytest pytest-cov && pytest --cov=main --cov=app --cov-branch .
pip install flake8 && flake8 ./*.py ./app/*.py ./tests/*.py
pip install mypy types-requests && mypy ./*.py ./app/*.py ./tests/*.py
