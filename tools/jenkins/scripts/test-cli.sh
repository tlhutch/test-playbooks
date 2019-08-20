#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-''}
INVENTORY=${INVENTORY:-''}
TOWER_FORK=${TOWER_FORK:-'ansible'}
TOWER_BRANCH=${TOWER_BRANCH:-'devel'}
PRODUCT=${PRODUCT:-'awx'}
AWXKIT_FORK=${TOWERKIT_FORK:-${TOWER_FORK}}
AWXKIT_BRANCH=${TOWERKIT_BRANCH:-${TOWER_BRANCH}}
AWXKIT_REPO=${AWXKIT_REPO:-${PRODUCT}}
VARS_FILE=${VARS_FILE:-playbooks/vars.yml}
PYTEST_NUMPROCESSES="4"

source "$(dirname "${0}")"/lib/common

setup_python3_env

pip install -Ur scripts/requirements.install
pip install -Ur requirements.txt

# In future use RPM install
pip install -U "git+ssh://git@github.com/${AWXKIT_FORK}/${AWXKIT_REPO}.git@${AWXKIT_BRANCH}#egg=awxkit[formatting,websockets]&subdirectory=awxkit"

if [[ -z "${INVENTORY}" ]]; then
    INVENTORY=$(retrieve_inventory_file)
fi
TOWER_HOST=$(retrieve_tower_server_from_inventory "${INVENTORY}")
CREDS=$(retrieve_credential_file "${INVENTORY}")

set +e

pytest -v -c config/api.cfg \
    --junit-xml=reports/junit/results-cli.xml \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    --base-url="https://${TOWER_HOST}" \
    -n "${PYTEST_NUMPROCESSES}" \
    -k "${TESTEXPR}" \
    tests/cli

set -e
