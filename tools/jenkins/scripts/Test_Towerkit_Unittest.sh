#!/usr/bin/env bash
set -euxo pipefail

pip install pytest==3.1.1
pip install tox
tox
