#!/usr/bin/env bash

mkdir -p ~/.ssh/
cp $PUBLIC_KEY ~/.ssh/id_rsa.pub

# Enable junit XML output
# export ANSIBLE_CALLBACK_PLUGINS="playbooks/library/callbacks"

pip install pip==9.0.2 # temp workaround for pip 10
pip install -U setuptools #pip
pip install -U setuptools pbr
pip install -U -I pyrax boto boto3 botocore azure apache-libcloud
pip install -U -I argparse # required by pyrax -> novaclient, but not explicitly listed
pip install -U -I junit-xml

pip uninstall -y ansible

if [[ "${ANSIBLE_INSTALL_METHOD}" == nightly ]]; then
    pip install -U -I "${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_NIGHTLY_BRANCH}/tar/ansible-latest.tar.gz"
else
    pip install -U -I ansible
fi


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


MINIMUM_VAR_SPACE=0 \
INSTANCE_NAME_PREFIX="${INSTANCE_NAME_PREFIX}-ansible-${ANSIBLE_NIGHTLY_BRANCH}" \
ANSIBLE_NIGHTLY_REPO="${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_NIGHTLY_BRANCH}" \
python scripts/cloud_vars_from_env.py --cloud-provider ${CLOUD_PROVIDER} --platform ${PLATFORM} > playbooks/vars.yml
ansible-playbook -i playbooks/inventory -e @playbooks/vars.yml playbooks/deploy-tower.yml

# Changes to job parameters don't persist across shell sections; create .downstream_build_params here to pick up changes to INSTANCE_NAME_PREFIX
if [[ $TRIGGER == true ]]; then
cat << EOF > .trigger
INSTANCE_NAME_PREFIX=${INSTANCE_NAME_PREFIX}    
EOF
fi
