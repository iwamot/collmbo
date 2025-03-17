#!/bin/bash
pip install -r requirements.txt
pip install black && black ./*.py ./app/*.py ./tests/*.py
pip install pytest pytest-cov && pytest --cov=main --cov=app .
pip install flake8 && flake8 ./*.py ./app/*.py ./tests/*.py
pip install mypy boto3 types-requests && mypy ./*.py ./app/*.py ./tests/*.py
