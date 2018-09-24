#!/usr/bin/env bash

pip install -U setuptools pbr
pip install -r requirements.txt

if [[ "${ANSIBLE_INSTALL_METHOD}" == nightly ]]; then
    pip uninstall --yes ansible
    pip install "${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_NIGHTLY_BRANCH}/tar/ansible-latest.tar.gz"
else
    pip install ansible
fi

# extract tower hostname from upstream build artifact
ANSIBLE_INVENTORY=playbooks/inventory.log
INVENTORY_GROUP="${PLATFORM}:&${CLOUD_PROVIDER}"
INVENTORY_HOST=$(ansible -i ${ANSIBLE_INVENTORY} --list-hosts ${INVENTORY_GROUP} | tail -n 1 | awk 'NR==1{print $1}')


# decrypt credentials
ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml

# temp force pip install requests
pip install requests==2.19.0

# determine if any ansible issues are still unresolved
py.test -c config/api.cfg --ansible-host-pattern="${INVENTORY_HOST}" --ansible-inventory="${ANSIBLE_INVENTORY}" -k "${TESTEXPR}" --base-url="https://${INVENTORY_HOST}" --github-summary tests/api > github_issues.txt
sed -i '/github issue report/,/generated xml file/!d' github_issues.txt
sed -i '/generated xml file/d' github_issues.txt
cp github_issues.txt github_issues.unresolved
sed -i '/Resolved/,$d' github_issues.unresolved

export PYTEST_ARGS="${PYTEST_ARGS} --mp --np ${PYTEST_MP_PROCESSES}"

run_tests_and_generate_html(){
    set +e
    py.test ${PYTEST_ARGS} \
    -c config/api.cfg \
    --ansible-host-pattern="${INVENTORY_HOST}" \
    --ansible-inventory="${ANSIBLE_INVENTORY}" \
    -k "${TESTEXPR}" \
    --base-url="https://${INVENTORY_HOST}" \
    tests/api
    
    TEST_STATUS=$?

    mkdir -p reports/html
    junit2html reports/junit/results.xml reports/html/index.html

    set -e
    return $TEST_STATUS
}
run_tests_and_generate_html
