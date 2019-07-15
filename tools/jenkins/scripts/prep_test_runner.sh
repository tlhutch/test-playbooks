#!/usr/bin/env bash
#
# prep_test_runner.sh: The goal of this script is to deploy
# the test-runner node with the proper content setup on this
# node.
#
# When run via Jenkins, one will have access to inventory.test_runner
# and test_runner_host artifacts

set -euxo pipefail

PUBLIC_KEY=${PUBLIC_KEY:=''}
JSON_KEY_FILE=${JSON_KEY_FILE:=''}
VAULT_FILE=${VAULT_FILE:=''}


mkdir -p ~/.ssh && cp ${PUBLIC_KEY} ~/.ssh/id_rsa.pub
cp ${JSON_KEY_FILE} json_key_file

ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml
ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials-pkcs8.vault --output=config/credentials-pkcs8.yml || true

# Generate variable file for the test-runner itself
SCENARIO=test_runner ./tools/jenkins/scripts/generate_vars.sh

# Generate variable file for the tower deployment to deploy
./tools/jenkins/scripts/generate_vars.sh

ansible-playbook -v \
    -i playbooks/inventory \
    -e @playbooks/test_runner_vars.yml \
    playbooks/deploy-test-runner.yml

mkdir -p artifacts
cat playbooks/inventory.test_runner | tee artifacts/inventory.test_runner
grep -A 1 test-runner playbooks/inventory.test_runner | tail -n 1 | cut -d" " -f1 > artifacts/test_runner_host
