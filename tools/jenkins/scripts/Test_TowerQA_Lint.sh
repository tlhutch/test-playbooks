#!/usr/bin/env bash
set -euxo pipefail

pip install -U pip
pip install -r requirements.txt
pip install setuptools-lint

pycodestyle --config=.flake8 . | tee pycodestyle.log

flake8 --output-file=flake8.log || :
