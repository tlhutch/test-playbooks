#!/usr/bin/env bash
set -euxo pipefail

# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common
setup_python3_env betelgeuse

pip install -qU betelgeuse click junitparser requests

# Ensure results are merged and classnames updated properly
./scripts/merge_junit artifacts/results.xml artifacts/results-cli.xml results-merged.xml
./scripts/update_junit_classname results-merged.xml test-run-results.xml

# Import requirements
./tools/betelgeuse/scripts/polarion-import requirement tools/betelgeuse/requirements.xml

# Generate test cases and import them
./tools/betelgeuse/scripts/gen-test-cases
./tools/betelgeuse/scripts/polarion-import testcase reports/betelgeuse/test-cases.xml

# Generate test run and import it
./tools/betelgeuse/scripts/gen-test-run
./tools/betelgeuse/scripts/polarion-import xunit reports/betelgeuse/test-run.xml
