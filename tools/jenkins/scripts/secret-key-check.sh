#!/usr/bin/env bash
set -euxo pipefail

# shellcheck source=lib/common
source "$(dirname "${0}")/lib/common"

INVENTORY="$(retrieve_inventory_file)"

ansible tower \
    -i "${INVENTORY}" \
    -a "cat /etc/tower/SECRET_KEY" \
    -e ansible_become=true
