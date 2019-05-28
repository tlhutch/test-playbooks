#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-''}
VARS_FILE=${VARS_FILE:-playbooks/vars.yml}

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env

pip install -Ur scripts/requirements.install
pip install -Ur requirements.txt

INVENTORY=$(retrieve_inventory_file)
TOWER_HOST=$(retrieve_tower_server_from_inventory "${INVENTORY}")
CREDS=$(retrieve_credential_file "${INVENTORY}")
ANSIBLE_VERSION=$(retrieve_value_from_vars_file "${VARS_FILE}" ansible_nightly_branch)

set +e

pytest -c config/api.cfg \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    -k "${TESTEXPR}" --base-url="https://${TOWER_HOST}"

sleep 360

pytest -c config/api.cfg \
    --last-failed --last-failed-no-failures none \
    --junit-xml=reports/junit/results-rerun.xml \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    -k "${TESTEXPR}" --base-url="https://${TOWER_HOST}"

python scripts/override_junit.py reports/junit/results.xml reports/junit/results-rerun.xml reports/junit/results-final.xml

set -e
