#!/usr/bin/env bash
set -euxo pipefail

rm -f ./run_integration_tests

if [[ ${sha1} =~ /pr/([0-9]+) ]]
then
  PULL_ID_FROM_BRANCH=${BASH_REMATCH[1]}
fi

ghprbPullId=${ghprbPullId:-${PULL_ID_FROM_BRANCH}}

# Build & run if not testing against a pr
if [ -z "$ghprbPullId" ]
then
  touch ./run_integration_tests
  exit
fi

GH_API_PR_LABEL_URL=https://api.github.com/repos/ansible/tower-qa/issues/${ghprbPullId}/labels
INTEGRATION_LABEL=`curl -u :${GITHUB_ACCESS_TOKEN} ${GH_API_PR_LABEL_URL} 2>/dev/null | grep -c 'ci:integration'` || true
if [ ${INTEGRATION_LABEL} -gt 0 ]
then
  touch ./run_integration_tests
fi


if [[ -e "./run_integration_tests" ]]; then

    cd $WORKSPACE
    mkdir -p ~/.ssh/
    cp $PUBLIC_KEY ~/.ssh/id_rsa.pub
    if [ "$(grep -s "python3" tox.ini)" ]; then
    python3 -m venv $PWD/venv
    source $PWD/venv/bin/activate
    fi
    which python
    python --version

    pip install -Ur scripts/requirements.install

    # Increase ssh timeout
    export ANSIBLE_TIMEOUT=30

    # return to kansas
    export ANSIBLE_NOCOLOR=True

    #
    # Install Tower
    #

    export INSTANCE_NAME_PREFIX=${INSTANCE_NAME_PREFIX}-`echo ${sha1} | sed -e 's,/,_,g'`
    MINIMUM_VAR_SPACE=0 \
    ANSIBLE_NIGHTLY_REPO="${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_NIGHTLY_BRANCH}" \
    python scripts/cloud_vars_from_env.py --cloud-provider ${CLOUD_PROVIDER} --platform ${PLATFORM} > vars.yml
    ansible-playbook -i playbooks/inventory -e @vars.yml playbooks/deploy-tower.yml

    TOWER_URL=`ansible -i playbooks/inventory.log --list-hosts tower | grep -v -m 1 hosts | xargs`
    TOWER_VERSION=`curl -ks https://${TOWER_URL}/api/v1/ping/ | jq -r .version | cut -d . -f 1-3`
    echo ${TOWER_VERSION}

    #
    # Run Tests
    #

    # extract tower hostname
    ANSIBLE_INVENTORY=playbooks/inventory.log
    INVENTORY_GROUP="${PLATFORM}:&${CLOUD_PROVIDER}"
    INVENTORY_HOST=$(ansible -i ${ANSIBLE_INVENTORY} --list-hosts ${INVENTORY_GROUP} | tail -n 1 | awk 'NR==1{print $1}')

    # decrypt credentials
    ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml

    run_tests_and_generate_html(){
        set +e
    	py.test ${PYTEST_ARGS} \
        -c config/api.cfg \
        --ansible-host-pattern="${INVENTORY_HOST}" \
        --ansible-inventory="${ANSIBLE_INVENTORY}" \
        --base-url="https://${INVENTORY_HOST}" \
        --mp --np 4 \
        tests/api

        TEST_STATUS=$?

        mkdir -p reports/html
        junit2html reports/junit/results.xml reports/html/index.html
        ansible-playbook -i playbooks/inventory.log -e @vars.yml playbooks/reap-tower-ec2.yml

    	set -e
        return $TEST_STATUS
    }
    run_tests_and_generate_html

    echo "### DESTROY CLOUD ###"
    bash -e scripts/jenkins_runplay.sh playbooks/destroy.yml | tee destroy.log

fi
