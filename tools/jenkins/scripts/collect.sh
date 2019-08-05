#!/usr/bin/env bash

set -euxo pipefail

INVENTORY=${INVENTORY:-''}

# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env

pip install -U ansible

if [[ -z "${INVENTORY}" ]]; then
    INVENTORY=$(retrieve_inventory_file)
fi

set +e

ansible-playbook -i ${INVENTORY} playbooks/collect_artifacts.yml

set -e
