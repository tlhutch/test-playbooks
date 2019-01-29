#!/usr/bin/env bash

set -euxo pipefail

DATA=${DATA:-scripts/resource_loading/data_latest_loading.yml}

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

INVENTORY=$(retrieve_inventory_file)
TOWER_HOST="$(retrieve_tower_server_from_inventory "${INVENTORY}")"
CREDS=$(retrieve_credential_file "${INVENTORY}")
TOWER_URL="https://${TOWER_HOST}"
until is_tower_ready "${TOWER_URL}"; do :; done

scripts/resource_loading/load_tower.py \
    --inventory "${INVENTORY}" \
    --credentials "${CREDS}" \
    --resources "${DATA}"
