#!/usr/bin/env bash

set -euxo pipefail

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

INVENTORY=$(retrieve_inventory_file)

if [[ -e "${INVENTORY}" ]]; then
    ansible-playbook -i "${INVENTORY}" -e @playbooks/vars.yml playbooks/reap-tower-ec2.yml || true
else
    >&2 echo "No inventory found. No instance to clean up."
fi
