#!/usr/bin/env bash -xe
###############################################################################
#
# Description:
#  * Helper script to contruct a vars.yml and run the playbook specified
#
# Author:
#  * James Laska <jlaska@ansible.com>
#
###############################################################################

#
# Generate a random password
#
gen_passwd() {
    # tr -dc A-Za-z0-9_ < /dev/urandom | head -c 16
    openssl rand -base64 8 | md5sum | head -c10
}

#
# Convenience function to load images from playbooks/group_vars/all
#
filter_images() {
    python scripts/image_deploy_vars.py --cloud_provider ${1} --platform ${2} --ansible_version ${3} ${4}
}

# Determine which playbook was requested
if [ $# -ne 1 ]; then
    echo "Usage: $0 <path/playbook.yml>"
    exit 1
fi

PLAYBOOK_PATH=${1}
PLAYBOOK_DIR=$(dirname ${PLAYBOOK_PATH})
PLAYBOOK=$(basename ${PLAYBOOK_PATH})

# Assert expected environment variables exist
for VARNAME in JOB_NAME JENKINS_HOME ;
do
    if [ -z "${!VARNAME}" ]; then
        echo "ERROR: variable $VARNAME undefined"
        exit 1
    fi
done

# Create json argument file
cat << EOF >${PLAYBOOK_DIR}/vars.yml
---
EOF

# Append desired variables to argument file.  This looks through the current
# `env` and stores variables matching a pattern
OFS="$IFS"
IFS=$'\n'
for LINE in $(env) ; do
    IFS="="
    set -- $LINE
    VARNAME="$1"
    case $VARNAME in
        DELETE_ON_START|MINIMUM_VAR_SPACE)
            echo "${VARNAME,,}: ${!VARNAME}" >> ${PLAYBOOK_DIR}/vars.yml
            ;;
        AWX*|AW_*|GALAXY*|ANSIBLE*|AWS*|EC2*|GCE*|AZURE*|INSTANCE*|CREATE_EC2*|TERMINATE_EC2*)
            echo "${VARNAME,,}: '${!VARNAME}'" >> ${PLAYBOOK_DIR}/vars.yml
            ;;
        *)
            echo "Ignoring environment variable: $VARNAME"
            ;;
    esac
done
# Without unsetting field separators, expected future variable functionality is in jeopardy
unset IFS
unset OFS

# # Establish the aw_repo_url.  This is the baseurl used by the install playbook.
# # If OFFICIAL=yes, use the public repository. Otherwise, use the nightly
# # repository.
# case "${OFFICIAL}" in
#     [Yy]es|[Tt]rue)
#         echo "aw_repo_url: http://releases.ansible.com/ansible-tower" >> ${PLAYBOOK_DIR}/vars.yml
#         ;;
#     *)
#         # Including GIT_BRANCH allows using an aw_repo_url to install builds
#         # from branches
#         echo "aw_repo_url: http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/${GIT_BRANCH#*/}" >> ${PLAYBOOK_DIR}/vars.yml
#         ;;
# esac

# Determine which distros to deploy
case ${CLOUD_PROVIDER}-${PLATFORM} in
    # All ec2 distros
    ec2-all)
        GCE_IMAGES="[]"
        AZURE_IMAGES="[]"
        ;;
    # A specific ec2 distro
    ec2-*)
        GCE_IMAGES="[]"
        AZURE_IMAGES="[]"
        # use desired ec2 distro
        EC2_IMAGES=$(filter_images ec2 ${PLATFORM} ${ANSIBLE_NIGHTLY_BRANCH} "${FILTER_IMAGE_EXTRA_ARGS}")
        ;;
    # All gce distros
    gce-all)
        EC2_IMAGES="[]"
        AZURE_IMAGES="[]"
        ;;
    # A specific gce distro
    gce-*)
        EC2_IMAGES="[]"
        AZURE_IMAGES="[]"
        # use desired gce distro
        GCE_IMAGES=$(filter_images gce ${PLATFORM} ${ANSIBLE_NIGHTLY_BRANCH} "${FILTER_IMAGE_EXTRA_ARGS}")
        ;;
    # All azure distros
    azure-all)
        EC2_IMAGES="[]"
        GCE_IMAGES="[]"
        ;;
    # A specific azure distro
    azure-*)
        EC2_IMAGES="[]"
        GCE_IMAGES="[]"
        # use desired azure distro
        AZURE_IMAGES=$(filter_images azure ${PLATFORM} ${ANSIBLE_NIGHTLY_BRANCH} "${FILTER_IMAGE_EXTRA_ARGS}")
        ;;
    all-all)
        # the default is all clouds, all distros ... no action required
        ;;
    all-*)
        EC2_IMAGES=$(filter_images ec2 ${PLATFORM} ${ANSIBLE_NIGHTLY_BRANCH} "${FILTER_IMAGE_EXTRA_ARGS}")
        GCE_IMAGES=$(filter_images gce ${PLATFORM} ${ANSIBLE_NIGHTLY_BRANCH} "${FILTER_IMAGE_EXTRA_ARGS}")
        AZURE_IMAGES=$(filter_images azure ${PLATFORM} ${ANSIBLE_NIGHTLY_BRANCH} "${FILTER_IMAGE_EXTRA_ARGS}")
        ;;
    *)
        # the default is all clouds, all distros ... no action required
        ;;
esac

# If custom distros are needed, save them in ${PLAYBOOK_DIR}/vars.yml
if [ -n "${EC2_IMAGES}" ]; then
    echo "ec2_images: ${EC2_IMAGES}" >> ${PLAYBOOK_DIR}/vars.yml
fi
if [ -n "${GCE_IMAGES}" ]; then
    echo "gce_images: ${GCE_IMAGES}" >> ${PLAYBOOK_DIR}/vars.yml
fi
if [ -n "${AZURE_IMAGES}" ]; then
    echo "azure_images: ${AZURE_IMAGES}" >> ${PLAYBOOK_DIR}/vars.yml
fi

#
# Custom awx passwords?  If no password is provided, a random password will be
# created
#

AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD-$(gen_passwd)}
if [ -n "${AWX_ADMIN_PASSWORD}" ]; then
    echo "admin_password: ${AWX_ADMIN_PASSWORD}" >> ${PLAYBOOK_DIR}/vars.yml
fi

AWX_PG_PASSWORD=${AWX_PG_PASSWORD-$(gen_passwd)}
if [ -n "${AWX_PG_PASSWORD}" ]; then
    echo "pg_password: ${AWX_PG_PASSWORD}" >> ${PLAYBOOK_DIR}/vars.yml
fi

AWX_RABBITMQ_PASSWORD=${AWX_RABBITMQ_PASSWORD-$(gen_passwd)}
if [ -n "${AWX_RABBITMQ_PASSWORD}" ]; then
    echo "rabbitmq_password: ${AWX_RABBITMQ_PASSWORD}" >> ${PLAYBOOK_DIR}/vars.yml
fi

# Add custom ssh pubkeys
if [ -n "${AUTHORIZED_KEYS}" ]; then
    echo "authorized_keys: " >> ${PLAYBOOK_DIR}/vars.yml
    echo "${AUTHORIZED_KEYS}" | while read LINE;
    do
        test -z "${LINE}" && continue
        echo  "  - '${LINE}'" >> ${PLAYBOOK_DIR}/vars.yml
    done
fi

export ANSIBLE_HOST_KEY_CHECKING=False      # Disable strict host key checking
export ANSIBLE_RETRY_FILES_ENABLED=False    # Disable .retry files

# How much verbosity do you want ...
if [[ "${VERBOSE}" == true ]]; then
  ARGS="-vvvv"
else
  ARGS="-v"
fi

ansible-playbook ${ARGS} -i ${PLAYBOOK_DIR}/inventory -e @${PLAYBOOK_DIR}/vars.yml "${PLAYBOOK_PATH}"

exit $?
