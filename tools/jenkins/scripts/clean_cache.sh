#!/usr/bin/env bash

set -euxo pipefail

VARS_FILE=${VARS_FILE:-playbooks/vars.yml}

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

INVENTORY=$(retrieve_inventory_file)

ansible cloud -i "${INVENTORY}" -m shell -a 'yum --enablerepo=ansible-tower,ansible-tower-dependencies clean all || true' -e ansible_become=true

# NOTE(spredzy): To put somewhere else
sed -i '/delete_on_start/d' "${VARS_FILE}"
echo "awx_upgrade: 'true'" >> "${VARS_FILE}"
echo "delete_on_start: 'false'" >> "${VARS_FILE}"
