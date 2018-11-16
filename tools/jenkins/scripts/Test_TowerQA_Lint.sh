#!/usr/bin/env bash
set -euxo pipefail

pip install -U pip
pip install -r requirements.txt
pip install setuptools-lint

pep8 --config=.flake8 . | tee pep8.log

flake8 --output-file=flake8.log || :
