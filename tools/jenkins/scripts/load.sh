#!/usr/bin/env bash

set -euxo pipefail

# Enable python3 if this version of tower-qa uses it
if [ "$(grep -s "python3" tox.ini)" ]; then
python3 -m venv $PWD/venv
source $PWD/venv/bin/activate
fi

pip install -Ur scripts/requirements.install

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
