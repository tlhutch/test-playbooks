#!/usr/bin/env bash
set -e
set -u
set -o pipefail

find . -type f -regex ".*\.py[co]$$" -delete
find . -path '*/__pycache__/*' -delete
find . -type d -name '__pycache__' -empty -delete
