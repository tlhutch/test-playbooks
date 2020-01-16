#!/usr/bin/env bash

set -euxo pipefail

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env

pip install -Ur scripts/requirements.install
pip install -Ur requirements.txt

echo "y" | pip uninstall pytest-mp || true

until is_tower_ready "${TOWER_HOST}"; do sleep 10; done

INVENTORY=$(retrieve_inventory_file)
TOWER_HOST="$(retrieve_tower_server_from_inventory "${INVENTORY}")"
CREDS=$(retrieve_credential_file "${INVENTORY}")
until is_tower_ready "https://${TOWER_HOST}"; do :; done

pytest -c config/verify.cfg \
    --api-credentials="${CREDS}" \
    --base-url="https://${TOWER_HOST}"
