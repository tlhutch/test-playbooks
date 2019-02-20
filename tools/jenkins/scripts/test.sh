#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-'test_crawler or ansible_integration'}


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

set +e

pytest -c config/api.cfg \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    -k "${TESTEXPR}" --base-url="https://${TOWER_HOST}"

set -e
