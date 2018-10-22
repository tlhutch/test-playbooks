#!/bin/bash -xe

mkdir -p ~/.ssh/
cp $PUBLIC_KEY ~/.ssh/id_rsa.pub

pip install pip==9.0.2

pip install -U setuptools #pip
pip install -U -I boto boto3 botocore azure apache-libcloud
pip install -U -I junit-xml

export ANSIBLE_TIMEOUT=30
export ANSIBLE_RETRY_FILES_ENABLED=False
export CLUSTER_SETUP=True

staging_repo_regex=".*releases-master.ansible.com.*"
release_branch_regex=".*release_([0-9]\.[0-9]\.[1-9])"
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

python scripts/cloud_vars_from_env.py --cloud-provider ec2 --image-vars ${IMAGES_FILE_PATH} --platform ${PLATFORM} > cloud_vars.yml

ansible-playbook \
-i playbooks/inventory \
-e @cloud_vars.yml \
-e ec2_key_name=jenkins \
-e ec2_public_key="{{ lookup('file', '~/.ssh/id_rsa.pub') }}" \
-e delete_on_start=${DELETE_ON_START} \
-e create_ec2_wait_upon_creation=true \
-e terminate_ec2_wait_upon_creation=false \
-e awx_upgrade=false \
-e minimum_var_space=0 \
-e instance_name_prefix=${INSTANCE_NAME_PREFIX} \
-e gpgcheck=0 \
-e pendo_state=off \
-e ansible_nightly_repo=${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_NIGHTLY_BRANCH} \
-e aw_repo_url=${AW_REPO_URL} \
-e awx_setup_path=${AWX_SETUP_PATH} \
-e ansible_install_method=${ANSIBLE_INSTALL_METHOD} \
-e admin_password=${AWX_ADMIN_PASSWORD} \
-e pg_password=${AWX_ADMIN_PASSWORD} \
${TOWER_INSTALL_PLAYBOOK}

# Ansible was moved from EPEL to RHEL Extras (and to releases.ansible.com) - need to update OOB install steps
# -e out_of_box_os=true \

cat << EOF > .downstream_build_params
PLATFORM=${PLATFORM}
ANSIBLE_NIGHTLY_BRANCH=${ANSIBLE_NIGHTLY_BRANCH}
INSTANCE_NAME_PREFIX=${INSTANCE_NAME_PREFIX}
EOF

TOWER_URL=`python scripts/ansible_inventory_to_json.py --inventory ${INVENTORY_FILE} | jq -r .tower\[0\]`
TOWER_VERSION=`curl -ks https://${TOWER_URL}/api/v1/ping/ | jq -r .version | cut -d . -f 1-3`
echo ${TOWER_VERSION}

TRIGGER_FILE=".trigger"

if [[ $TRIGGER == true ]]; then mv .downstream_build_params ${TRIGGER_FILE}; fi;
