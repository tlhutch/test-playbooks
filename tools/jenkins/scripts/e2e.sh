#!/usr/bin/env bash

set -euxo pipefail

TEST_SELECTION=${TEST_SELECTION:-'*'}
VARS_FILE=${VARS_FILE:-playbooks/vars.yml}
JSON_KEY_FILE_PATH=${JSON_KEY_FILE_PATH:-json_key_file}


# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

INVENTORY=$(retrieve_inventory_file)
TOWER_URL="https://$(retrieve_tower_server_from_inventory "${INVENTORY}")"
DEPLOYMENT_TYPE=$(retrieve_deployment_type "${TOWER_URL}")
AWX_ADMIN_PASSWORD=$(retrieve_value_from_vars_file "${VARS_FILE}" admin_password)


if [[ "$DEPLOYMENT_TYPE" == "tower" ]]; then
    curl -o add_license.py https://gist.githubusercontent.com/jakemcdermott/0aac520c7bb631ee46517dfab94bd6dd/raw/fd85fdad7395f90ac4acab1b6c2edf10df0bb3d7/apply_license.py
    python add_license.py -u admin -p "${AWX_ADMIN_PASSWORD}" "${TOWER_URL}"
    CONTAINER_IMAGE_NAME=tower_e2e
else
    CONTAINER_IMAGE_NAME=awx_e2e
fi


docker login -u _json_key -p "$(cat "${JSON_KEY_FILE_PATH}")" https://gcr.io
docker pull gcr.io/ansible-tower-engineering/"${CONTAINER_IMAGE_NAME}":latest
docker tag gcr.io/ansible-tower-engineering/"${CONTAINER_IMAGE_NAME}":latest  awx_e2e:latest
docker-compose -f tower/awx/ui/test/e2e/cluster/docker-compose.yml run \
    -e AWX_E2E_URL="${TOWER_URL}" \
    -e AWX_E2E_USERNAME=admin \
    -e AWX_E2E_PASSWORD="${AWX_ADMIN_PASSWORD}" \
    e2e --filter="${TEST_SELECTION}"
