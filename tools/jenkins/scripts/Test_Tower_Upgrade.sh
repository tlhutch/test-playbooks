#!/bin/bash -xe -o pipefail

yum remove -y python-requests

pip install -U appdirs # https://github.com/ActiveState/appdirs/issues/89
pip install -U pip setuptools ansible
pip install -Ir requirements.txt


## default ssh public key
mkdir -p ~/.ssh/
cp $PUBLIC_KEY ~/.ssh/id_rsa.pub


ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml


export ANSIBLE_HOST_KEY_CHECKING=False
export ANSIBLE_TIMEOUT=30
export ANSIBLE_PACKAGE_NAME="ansible"
export PYTHONUNBUFFERED=1


if [[ "${VERBOSE}" == true ]]; then
    VERBOSITY="-vvvv"
else
    VERBOSITY="-v"
fi


env



cat << EOF > install_vars.yml
---
admin_password: ${AWX_ADMIN_PASSWORD}
ansible_install_method: ${ANSIBLE_INSTALL_METHOD}
ansible_nightly_repo: ${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_BRANCH}
ansible_package_name: ${ANSIBLE_PACKAGE_NAME}
aw_repo_url: ${INSTALL_AW_REPO_URL}
awx_setup_path: ${INSTALL_AWX_SETUP_PATH}
create_ec2_wait_upon_creation: false
delete_on_start: ${DELETE_ON_INSTALL}
create_ec2_assign_public_ip: true
create_ec2_vpc_id: vpc-552da032
create_ec2_vpc_subnet_id: subnet-9cdddbb0
ec2_images: `scripts/image_deploy_vars.py --cloud_provider ${CLOUD_PROVIDER} --platform ${PLATFORM} --ansible_version ${ANSIBLE_BRANCH} --groups tower`
instance_name_prefix: ${INSTANCE_NAME_PREFIX}-ansible-${ANSIBLE_BRANCH}
minimum_var_space: 0
pg_password: ${AWX_PG_PASSWORD}
terminate_ec2_wait_upon_creation: false
EOF


function reap_instances {
    echo "### Reap EC2 Instances ###"
    ansible-playbook ${VERBOSITY} -i playbooks/inventory.log -e @install_vars.yml playbooks/reap-tower-ec2.yml || true
}


if [ "$REAP_INSTANCES" = true ]; then
    echo "### REAP_INSTANCES IS TRUE. DUN DUN DUUUNNNN ###"
    trap reap_instances EXIT
fi

if [ "$INSTALL" = true ]; then
    echo "### Install ###"
    #trap reap_instances EXIT
    ansible-playbook ${VERBOSITY} -i playbooks/inventory -e @install_vars.yml playbooks/${TOWER_INSTALL_PLAYBOOK} | tee 01-install.log
fi


if [ "$LOAD_TOWER" = true ]; then
    echo "### Load Tower ###"
    scripts/resource_loading/load_tower.py ${LOADING_ARGS} | tee 02-resource-loading.log
fi


cat << EOF > upgrade_vars.yml
---
admin_password: ${AWX_ADMIN_PASSWORD}
ansible_install_method: ${ANSIBLE_INSTALL_METHOD}
ansible_nightly_repo: ${ANSIBLE_NIGHTLY_REPO}/${ANSIBLE_BRANCH}
ansible_package_name: ${ANSIBLE_PACKAGE_NAME}
aw_repo_url: ${UPGRADE_AW_REPO_URL}
awx_setup_path: ${UPGRADE_AWX_SETUP_PATH}
awx_upgrade: true
delete_on_start: false
ec2_images: `scripts/image_deploy_vars.py --cloud_provider ${CLOUD_PROVIDER} --platform ${PLATFORM} --ansible_version ${ANSIBLE_BRANCH} --groups tower`
instance_name_prefix: ${INSTANCE_NAME_PREFIX}-ansible-${ANSIBLE_BRANCH}
minimum_var_space: 0
out_of_box_os: true
pg_password: ${AWX_PG_PASSWORD}
EOF

if [ "${SLEEP_BEFORE_UPGRADE}" = true ]; then
    echo "### Sleeping for ${SLEEP_BEFORE_UPGRADE_DURATION} seconds ###"
    sleep ${SLEEP_BEFORE_UPGRADE_DURATION}
fi

if [ "$UPGRADE" = true ]; then
    echo "### Upgrade ###"
    ansible-playbook ${VERBOSITY} -i playbooks/inventory -e @upgrade_vars.yml playbooks/${TOWER_INSTALL_PLAYBOOK} | tee 03-upgrade.log
fi


if [ "$VERIFY_RESOURCES" = true ]; then
	echo "### Verify Loaded Resources ###"
	scripts/resource_loading/verify_loaded_tower.py ${VERIFICATION_ARGS} | tee 04-resource-verification.log
fi
