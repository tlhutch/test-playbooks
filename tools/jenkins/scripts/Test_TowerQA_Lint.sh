#!/usr/bin/env bash
set -euxo pipefail

source "$(dirname "${0}")"/lib/common

setup_python3_env

which python
python --version

pip install -U tox

tox
