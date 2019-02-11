#!/usr/bin/env bash
set -euxo pipefail

if [ "$(grep -s "python3" tox.ini)" ]; then
python3 -m venv $PWD/venv
source $PWD/venv/bin/activate
fi
which python
python --version

pip install -Ur scripts/requirements.lint

tox
