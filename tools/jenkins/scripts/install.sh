#!/usr/bin/env bash

set -euxo pipefail

VARS_FILE=${VARS_FILE:-playbooks/vars.yml}

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env
local_python_path=$(command -v python)
pip install -U boto boto3 botocore pip ansible

PLAYBOOK=$(retrieve_value_from_vars_file "${VARS_FILE}" awx_playbook)
VERBOSITY=$(retrieve_value_from_vars_file "${VARS_FILE}" awx_verbosity)
INVENTORY=$(retrieve_value_from_vars_file "${VARS_FILE}" awx_inventory)

if [[ -f "${INVENTORY}" ]]; then
    _INVENTORY="${INVENTORY}"
    # NOTE(spredzy): Happily remove this code when either support of
    # stable-2.7 is dropped or Tower 3.4.x is dropped
    set +o pipefail
    rc=$(grep -e ansible_user "${INVENTORY}" | grep -v ansible_python_interpreter | wc -l)
    set -o pipefail
    if [[ "$rc" != "0" ]]; then
        if is_rhel8 "${VARS_FILE}"; then
            sed -i "s#\(.*ansible_user.*\)#\1 ansible_python_interpreter='/usr/libexec/platform-python'#g" "${INVENTORY}"
        else
            sed -i "s#\(.*ansible_user.*\)#\1 ansible_python_interpreter='/usr/bin/env python'#g" "${INVENTORY}"
        fi
    fi
else
    _INVENTORY="playbooks/inventory"
fi

# Ensure the localhost node is always using the python from the venv
sed -i "s#\(.*ansible_connection=local\).*#\1 ansible_python_interpreter='${local_python_path}'#g" "${_INVENTORY}"

ansible-playbook "${VERBOSITY}" -i "${_INVENTORY}" -e @"${VARS_FILE}" "${PLAYBOOK}"

TOWER_URL="https://$(retrieve_tower_server_from_inventory "${INVENTORY}")"
_TOWER_VERSION=$(curl -ks "${TOWER_URL}"/api/v2/ping/ | python -c 'import json,sys; print(json.loads(sys.stdin.read())["version"])' | cut -d . -f 1-3)

echo "${_TOWER_VERSION}"
echo "${TOWER_URL}" > tower_url
