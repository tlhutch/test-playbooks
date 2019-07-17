#!/usr/bin/env bash

set -euxo pipefail

INVENTORY=${INVENTORY:-''}

# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env

pip install -Ur scripts/requirements.install

if [[ -z "${INVENTORY}" ]]; then
    INVENTORY=$(retrieve_inventory_file)
fi

set +e

# Grab logs from tower instances
# By default will end up in playbooks/all_tower_sos_reports.tar.gz
ansible-playbook -i ${INVENTORY} playbooks/grab_tower_sos_reports.yml

set -e
