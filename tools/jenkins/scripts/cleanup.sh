#!/usr/bin/env bash

set -euxo pipefail

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env
local_python_path=$(command -v python)

pip install -U boto boto3 botocore ansible pip

INVENTORY=$(retrieve_inventory_file)
# Ensure the localhost node is always using the python from the venv (save inventory rewrite it)
sed -i "s#\(.*ansible_connection=local\).*#\1 ansible_python_interpreter='${local_python_path}'#g" "${INVENTORY}"


if [[ -e "${INVENTORY}" ]]; then
    ansible-playbook -i "${INVENTORY}" -e @playbooks/vars.yml playbooks/reap-tower-ec2.yml || true
else
    >&2 echo "No inventory found. No instance to clean up."
fi
