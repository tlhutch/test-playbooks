#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-''}
INVENTORY=${INVENTORY:-''}
AW_REPO_URL=${AW_REPO_URL:-''}
TOWER_FORK=${TOWER_FORK:-'ansible'}
TOWER_BRANCH=${TOWER_BRANCH:-'devel'}
PRODUCT=${PRODUCT:-'awx'}
AWXKIT_FORK=${TOWERKIT_FORK:-${TOWER_FORK}}
AWXKIT_BRANCH=${TOWERKIT_BRANCH:-${TOWER_BRANCH}}
AWXKIT_REPO=${AWXKIT_REPO:-${PRODUCT}}
VARS_FILE=${VARS_FILE:-playbooks/vars.yml}
PYTEST_NUMPROCESSES="8"

if [[ -n "${TESTEXPR}" ]]; then
    TESTEXPR=" and (${TESTEXPR})"
fi

source "$(dirname "${0}")"/lib/common
setup_python3_env

pip install -Ur scripts/requirements.install
pip install -Ur requirements.txt
pip install -U "git+ssh://git@github.com/${AWXKIT_FORK}/${AWXKIT_REPO}.git@${AWXKIT_BRANCH}#egg=awxkit[formatting,websockets]&subdirectory=awxkit"

if [[ -z "${AW_REPO_URL}" ]]; then
    AW_REPO_URL=$(retrieve_value_from_vars_file "${VARS_FILE}" aw_repo_url)
fi

if [[ -z "${INVENTORY}" ]]; then
    INVENTORY=$(retrieve_inventory_file)
fi
TOWER_HOST=$(retrieve_tower_server_from_inventory "${INVENTORY}")
CREDS=$(retrieve_credential_file "${INVENTORY}")

set +e

# Run tests that need to run serially
pytest -v -c config/api.cfg \
    --junit-xml=reports/junit/results-collection-serial.xml \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    --base-url="https://${TOWER_HOST}" \
    -k "serial${TESTEXPR}" \
    tests/collection

# Run parallel tests
pytest -v -c config/api.cfg \
    --junit-xml=reports/junit/results-collection-parallel.xml \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    --base-url="https://${TOWER_HOST}" \
    -n "${PYTEST_NUMPROCESSES}" \
    --dist=loadfile \
    -k "not serial${TESTEXPR}" \
    tests/collection

# Workaround https://github.com/pytest-dev/pytest-xdist/issues/445
./scripts/prefix_lastfailed "$(find .pytest_cache -name lastfailed)"
pytest --cache-show "cache/lastfailed"

# Rerun any failures to check for flake
pytest -v -c config/api.cfg \
    --last-failed --last-failed-no-failures none \
    --junit-xml=reports/junit/results-collection-rerun.xml \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    --base-url="https://${TOWER_HOST}" \
    tests/collection

./scripts/merge_junit \
    reports/junit/results{-collection-serial,-collection-parallel,-collection-rerun,-collection}.xml

set -e
