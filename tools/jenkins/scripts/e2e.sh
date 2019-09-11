#!/usr/bin/env bash

# e2e.sh does a run of the E2E UI testing suite.

# If you just want to use defaults and you have the following files,
# then you don't need to set any environment variables:

# If you don't have playbooks/inventory.cluster, then you need to define E2E_URL.
# DEPLOYMENT_TYPE is, at time of writing, always set to "tower" by default. You
# can change this to "awx" to skip trying to add a license.
# If you lack a playbooks/vars.yml, you can provide AWX_ADMIN_PASSWORD instead.
# If you lack a json_key_file, set SKIP_DOCKER_LOGIN to true and log in to docker
# before running this script.

# Full environment variable reference:

# - VARS_FILE: Defaults to "playbooks/vars.yml".
# - JSON_KEY_FILE_PATH. Defaults to "json_key_file". Used for docker login.
# - SKIP_DOCKER_LOGIN: Ignores json_key_file. You'll need to "docker login" manually.
# - DEPLOYMENT_TYPE: awx or tower. Currently defaults to tower.
# - SELENIUM_DOCKER_TAG: This is the tag used for selenium/node-chrome
#   and node/firefox images. Defaults to "latest".
# - AWX_ADMIN_PASSWORD: Manually provide this if you don't have a VARS_FILE
#   like playbooks/vars.yml.
# - E2E_URL: Target instance to test.
# - E2E_USERNAME: Login to use during tests. Defaults to "admin".
# - E2E_PASSWORD: Password for tests. Defaults to the value of AWX_ADMIN_PASSWORD.
#   Change this if you want to run E2E with a different user than admin.
# - E2E_FORK: Fork of repo to draw tests from. Defaults to "ansible".
# - E2E_BRANCH: Branch of repo to draw tests from. Defaults to "devel".
# - E2E_TEST_SELECTION: Test filter for nightwatch tests. Defaults to "*".
# - E2E_RETRIES: Number of times to retry a testsuite. Defaults to "2".
# - E2E_EXTERNAL_GRID_HOSTNAME: External selenium grid Hostname. Defaults to "localhost" to use local docker grid
# - E2E_EXTERNAL_GRID_PORT: Exteranl selenium grid port. Defaults to "4444"

set -euxo pipefail

VARS_FILE=${VARS_FILE:-playbooks/vars.yml}
JSON_KEY_FILE_PATH=${JSON_KEY_FILE_PATH:-json_key_file}

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

# If you're not using the vars file for docker credentials, set this to true. You'll need to auth before running the script.
SKIP_DOCKER_LOGIN=${SKIP_DOCKER_LOGIN:-false}

# Define your target E2E_URL ahead of time if you do not have a playbooks/inventory.cluster file
# generated to use for information.
if [[ -z "$E2E_URL" ]]; then
    INVENTORY=$(retrieve_inventory_file)
    echo "inventory used: $INVENTORY"
    E2E_URL="https://$(retrieve_tower_server_from_inventory "${INVENTORY}")"
    echo "E2E_URL retrieved from inventory is $E2E_URL"
fi

# A string, either awx or tower
if [[ -z "$DEPLOYMENT_TYPE" ]]; then
    DEPLOYMENT_TYPE=$(retrieve_deployment_type "${E2E_URL}")
fi

if [[ -z "$AWX_ADMIN_PASSWORD" ]]; then
    AWX_ADMIN_PASSWORD=$(retrieve_value_from_vars_file "${VARS_FILE}" admin_password)
fi

SELENIUM_DOCKER_TAG=${SELENIUM_DOCKER_TAG:-"latest"}

# Include https:// in URL. This is the URL the tests will target.
E2E_USERNAME=${E2E_USERNAME:-admin}
E2E_PASSWORD=${E2E_PASSWORD:-"$AWX_ADMIN_PASSWORD"}
E2E_FORK=${E2E_FORK:-"ansible"}
E2E_BRANCH=${E2E_BRANCH:-"devel"}
E2E_TEST_SELECTION=${E2E_TEST_SELECTION:-"*"}
E2E_RETRIES=${E2E_RETRIES:-"2"}

# Uses locally sourced chromedriver by default
E2E_EXTERNAL_GRID_HOSTNAME=${E2E_EXTERNAL_GRID_HOSTNAME:-$"hub"}
E2E_EXTERNAL_GRID_PORT=${E2E_EXTERNAL_GRID_PORT:-$"4444"}

git clone -b "${E2E_BRANCH}" git@github.com:"${E2E_FORK}"/"${DEPLOYMENT_TYPE}".git --depth 1 ${DEPLOYMENT_TYPE}

# if [[ "$DEPLOYMENT_TYPE" == "tower" ]]; then
  if [[ 1 ]]; then
    python "$(dirname "${0}")"/apply_license_py2.py -u admin -p "${AWX_ADMIN_PASSWORD}" "${E2E_URL}"
    CONTAINER_IMAGE_NAME=tower_e2e
else
    CONTAINER_IMAGE_NAME=awx_e2e
fi

# Only skip login if explicitly set to true
if ! [[ $SKIP_DOCKER_LOGIN == "true" ]]; then
    set +x
    docker login -u _json_key -p "$(cat "${JSON_KEY_FILE_PATH}")" https://gcr.io
    set -x
else
    echo "SKIP_DOCKER_LOGIN is set to true, skipping and going to the docker pull step"
fi
docker pull gcr.io/ansible-tower-engineering/"${CONTAINER_IMAGE_NAME}":latest
docker tag gcr.io/ansible-tower-engineering/"${CONTAINER_IMAGE_NAME}":latest ${CONTAINER_IMAGE_NAME}:latest

mkdir -p "${DEPLOYMENT_TYPE}/awx/ui/test/e2e/screenshots"

set +e
cp /root/.npmrc "${DEPLOYMENT_TYPE}/"
export NPMRC_FILE=.npmrc
docker-compose \
    -f "${DEPLOYMENT_TYPE}/awx/ui/test/e2e/cluster/docker-compose.yml" \
    run \
    -e AWX_E2E_CLUSTER_HOST="${E2E_EXTERNAL_GRID_HOSTNAME}" \
    -e AWX_E2E_CLUSTER_PORT="${E2E_EXTERNAL_GRID_PORT}" \
    -e AWX_E2E_URL="${E2E_URL}" \
    -e AWX_E2E_USERNAME="${E2E_USERNAME}" \
    -e AWX_E2E_PASSWORD="${E2E_PASSWORD}" \
    -e AWX_E2E_SCREENSHOTS_ENABLED=true \
    -e AWX_E2E_SCREENSHOTS_PATH="/awx/awx/ui/test/e2e/screenshots" \
    e2e --filter="${E2E_TEST_SELECTION}" \
    --suiteRetries="${E2E_RETRIES}"
set -e
