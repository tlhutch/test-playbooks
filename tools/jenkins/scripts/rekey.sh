#!/usr/bin/env bash
set -euxo pipefail

OPENSHIFT_DEPLOYMENT=${OPENSHIFT_DEPLOYMENT:-false}

# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

#TODO Rekey openshift
if [[ "${OPENSHIFT_DEPLOYMENT}" == "true" ]]; then
    ./setup/setup_openshift.sh -k -e @vars.yml -e ansible_become=true -e openshift_token="${OPENSHIFT_TOKEN}"
else
    INVENTORY=$(retrieve_inventory_file)
    INSTALL_NODE=$(retrieve_tower_server_from_inventory "${INVENTORY}")

    ansible "${INSTALL_NODE}" \
        -i "${INVENTORY}" \
        -a 'chdir=/tmp/setup ./setup.sh -k -e ansible_become=true -- -vvv' \
        -e ansible_become=true
fi
