#!/bin/bash -xe

mkdir -p ~/.ssh/
cp $PUBLIC_KEY ~/.ssh/id_rsa.pub

pip install -U pip setuptools
pip install -U setuptools
pip install sphinx==1.5.6
pip install -U pyrax boto boto3 botocore azure apache-libcloud
pip install -U argparse # required by pyrax -> novaclient, but not explicitly listed
pip install -U junit-xml

# Increase ssh timeout
export ANSIBLE_TIMEOUT=30

staging_repo_regex=".*releases-master.ansible.com.*"
release_branch_regex=".*release_([0-9]\.[0-9]\.[0-9])"
branch_regex=".*/([^/]*)$"

if [[ ${AW_REPO_URL} =~ ${staging_repo_regex} ]]; then
    INSTANCE_NAME_PREFIX="${INSTANCE_NAME_PREFIX}-staging-ansible-${ANSIBLE_NIGHTLY_BRANCH}"
elif [[ ${AW_REPO_URL} =~ ${release_branch_regex} ]]; then
    INSTANCE_NAME_PREFIX="${INSTANCE_NAME_PREFIX}-${BASH_REMATCH[1]}-ansible-${ANSIBLE_NIGHTLY_BRANCH}"
elif [[ ${AW_REPO_URL} =~ ${branch_regex} ]]; then
    INSTANCE_NAME_PREFIX="${INSTANCE_NAME_PREFIX}-${BASH_REMATCH[1]:0:15}-ansible-${ANSIBLE_NIGHTLY_BRANCH}"
else
    INSTANCE_NAME_PREFIX="${INSTANCE_NAME_PREFIX}-ansible-${ANSIBLE_NIGHTLY_BRANCH}"
fi


if [[ ${TOWERQA_GIT_BRANCH} =~ .*/release_3.2 ]]; then
    MINIMUM_VAR_SPACE=0 \
    ANSIBLE_NIGHTLY_REPO="${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_NIGHTLY_BRANCH}" \
    bash -xe scripts/jenkins_runplay.sh playbooks/deploy-tower.yml
else
    # https://github.com/ansible/tower-qa/pull/1583
    MINIMUM_VAR_SPACE=0 \
    ANSIBLE_NIGHTLY_REPO="${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_NIGHTLY_BRANCH}" \
    python scripts/cloud_vars_from_env.py --cloud-provider ${CLOUD_PROVIDER} --platform ${PLATFORM} > playbooks/vars.yml
    ansible-playbook -i playbooks/inventory -e @playbooks/vars.yml playbooks/deploy-tower.yml
fi

TOWER_URL=`python scripts/ansible_inventory_to_json.py --inventory playbooks/inventory.log | jq -r .tower\[0\]`
TOWER_VERSION=`curl -ks https://${TOWER_URL}/api/v1/ping/ | jq -r .version | cut -d . -f 1-3`
echo ${TOWER_VERSION}

if [[ ${TOWER_VERSION} =~ 3\.2\.[1-9].* ]]; then
    DOWNSTREAM_TOWERQA_GIT_BRANCH="origin/release_3.2"
    TRIGGER_FILE=".trigger_patch"
else
    DOWNSTREAM_TOWERQA_GIT_BRANCH="origin/master"
    TRIGGER_FILE=".trigger"
fi

# Changes to job parameters don't persist across shell sections; create .downstream_build_params here to pick up changes to INSTANCE_NAME_PREFIX
cat << EOF > .downstream_build_params
TOWERQA_GIT_BRANCH=${DOWNSTREAM_TOWERQA_GIT_BRANCH}
ANSIBLE_NIGHTLY_BRANCH=${ANSIBLE_NIGHTLY_BRANCH}
PLATFORM=${PLATFORM}
INSTANCE_NAME_PREFIX=${INSTANCE_NAME_PREFIX}
TEST_TOWER_INSTALL_BUILD=${BUILD_ID}
EOF

#
# Leave the tower url behind for downstream jobs that need it.
# As of 10/09/2018 only the yolo pipeline uses this for the e2e step.
#
echo ${TOWER_URL}
echo ${TOWER_URL} > .tower_url

if [[ $TRIGGER == true ]]; then mv .downstream_build_params ${TRIGGER_FILE}; fi;
