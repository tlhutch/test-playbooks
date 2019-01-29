#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-'test_crawler or ansible_integration'}


# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

INVENTORY=$(retrieve_inventory_file)
TOWER_HOST=$(retrieve_tower_server_from_inventory "${INVENTORY}")
CREDS=$(retrieve_credential_file "${INVENTORY}")

set +e

TOWERKIT_SCHEMA_VALIDATION=off pytest -c config/api.cfg \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    -k "${TESTEXPR}" --base-url="https://${TOWER_HOST}"

set -e
