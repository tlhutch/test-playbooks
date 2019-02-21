#!/usr/bin/env bash
set -euxo pipefail

mkdir -p ~/.ssh/
cp $PUBLIC_KEY ~/.ssh/id_rsa.pub

# Enable junit XML output
# export ANSIBLE_CALLBACK_PLUGINS="playbooks/library/callbacks"

# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common
setup_python3_env

pip install -Ur scripts/requirements.install

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

# Execute ansible --version on the tower host to find out exactly what got
# installed This is to help debug if we are getting the right builds because we
# have had trouble with stale RPMs in the past
ansible tower -i playbooks/inventory.log -m shell -a "ansible --version"  -e @playbooks/vars.yml -e ansible_user="{{ ec2_images[0].user }}" | tee ansible.version.output
# Also archive results of rpm -qa | grep ansible to get names of all ansible and ansible tower packages installed
ansible tower -i playbooks/inventory.log -m shell -a "rpm -qa | grep ansible"  -e @playbooks/vars.yml -e ansible_user="{{ ec2_images[0].user }}" | tee ansible.rpm.version

# Changes to job parameters don't persist across shell sections; create .downstream_build_params here to pick up changes to INSTANCE_NAME_PREFIX
if [[ $TRIGGER == true ]]; then
cat << EOF > .trigger
INSTANCE_NAME_PREFIX=${INSTANCE_NAME_PREFIX}
EOF
fi
