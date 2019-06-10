#!/usr/bin/env bash

set -euxo pipefail

VARS_FILE=${VARS_FILE:-playbooks/vars.yml}

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env
pip install -U boto boto3 botocore pip ansible

PLAYBOOK=$(retrieve_value_from_vars_file "${VARS_FILE}" awx_playbook)
VERBOSITY=$(retrieve_value_from_vars_file "${VARS_FILE}" awx_verbosity)
INVENTORY=$(retrieve_value_from_vars_file "${VARS_FILE}" awx_inventory)

ansible-playbook "${VERBOSITY}" -i playbooks/inventory -e @"${VARS_FILE}" "${PLAYBOOK}"

TOWER_URL="https://$(retrieve_tower_server_from_inventory "${INVENTORY}")"
_TOWER_VERSION=$(curl -ks "${TOWER_URL}"/api/v2/ping/ | python -c 'import json,sys; print(json.loads(sys.stdin.read())["version"])' | cut -d . -f 1-3)

echo "${_TOWER_VERSION}"
echo "${TOWER_URL}" > tower_url
