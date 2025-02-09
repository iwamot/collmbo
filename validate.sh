#!/bin/bash
pip install -r requirements.txt
pip install black && black ./*.py ./app/*.py ./tests/*.py
pip install pytest && pytest .
pip install flake8 && flake8 ./*.py ./app/*.py ./tests/*.py
pip install mypy boto3 && mypy ./*.py ./app/*.py ./tests/*.py
