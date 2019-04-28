#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-''}
TOWER_VERSION=${TOWER_VERSION:-'devel'}
SCENARIO=${SCENARIO:-'standalone'}
BUNDLE=${BUNDLE:-no}
AW_REPO_URL=${AW_REPO_URL:-http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/devel}
export PLATFORM=${PLATFORM:-'rhel-8.0-x86_64'}

# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml

setup_python3_env
pip install -U openstackclient ansible pip

# Export the necessary items for authentication
#
export OS_AUTH_URL=https://rhos-d.infra.prod.upshift.rdu2.redhat.com:13000/v3
export OS_PROJECT_ID=0ac6ff23baf344e78d6f81fb5d5b2aa8
export OS_PROJECT_NAME="ansible-tower"
export OS_USER_DOMAIN_NAME="redhat.com"
export OS_PROJECT_DOMAIN_ID="62cf1b5ec006489db99e2b0ebfb55f57"
export OS_USERNAME="yguenane"
export OS_REGION_NAME="regionOne"
export OS_ENDPOINT_TYPE=publicURL
export OS_IDENTITY_API_VERSION=3

AWX_SETUP_PATH=$(retrieve_awx_setup_path_based_on_version_and_scenario "${TOWER_VERSION}" "${SCENARIO}" "${AW_REPO_URL}" "${BUNDLE}" "${PLATFORM}") \
AWX_IPV6_DEPLOYMENT=no AWS_ACCESS_KEY=dummy AWS_SECRET_KEY=dummy ./tools/jenkins/scripts/generate_vars.sh

if [[ "${SCENARIO}" == "standalone" ]]; then
    ansible-playbook -v -i playbooks/inventory -e @playbooks/vars.yml -e aw_repo_url="${AW_REPO_URL}" playbooks/deploy-tower-rhel8.yml
else
    ansible-playbook -v -i playbooks/inventory -e @playbooks/vars.yml -e aw_repo_url="${AW_REPO_URL}" playbooks/deploy-tower-rhel8-cluster.yml
fi

if [[ "${RUN_TESTS}" == "true" ]]; then
    TESTEXPR="${TESTEXPR}" ./tools/jenkins/scripts/test.sh
fi
