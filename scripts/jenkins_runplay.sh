#!/bin/bash -xe
###############################################################################
#
# Description:
#  * Helper script to contruct a vars.yaml and run the site.yml play
#
# Author:
#  * James Laska <jlaska@ansibleworks.com>
#
###############################################################################

#
# Generate a random password
#
gen_passwd() {
    tr -dc A-Za-z0-9_ < /dev/urandom | head -c 16
}

#
# Convenience function to load images from playbooks/group_vars/all
#
filter_images() {
    # $1 = [ec2,rax,gce,azure]
    # $2 = [all,rhel,ubuntu,centos]
    python -c "import yaml; data = yaml.load(open('playbooks/group_vars/all','r')); print [i for i in data['${1}_images'] if '${2}' in i['name']]"
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
cat << EOF >${PLAYBOOK_DIR}/vars.yaml
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
        DELETE_ON_START|AWX_UPGRADE)
            echo "${VARNAME,,}: ${!VARNAME}" >> ${PLAYBOOK_DIR}/vars.yaml
            ;;
        AWX*|GALAXY*|AWS*|EC2*|RAX*|GCE*|AZURE*|INSTANCE*)
            echo "${VARNAME,,}: '${!VARNAME}'" >> ${PLAYBOOK_DIR}/vars.yaml
            ;;
        *)
            echo "Ignoring environment variable: $VARNAME"
            ;;
    esac
done

# Enable nightly ansible repository?
if [[ "${ENABLE_ANSIBLE_NIGHTLY_REPO}" == true ]]; then
    echo "ansible_nightly_repo: http://50.116.42.103/ansible_nightlies_QcGXFZKv5VfQHi" >> ${PLAYBOOK_DIR}/vars.yaml
fi

# Establish the aw_repo_url.  This is the baseurl used by the install playbook.
# If OFFICIAL=yes, use the public repository. Otherwise, use the nightly
# repository.
case "${PLAYBOOK}-${OFFICIAL}" in
    awx*-false|awx*-no|ansible-tower*-false|ansible-tower*-no)
        echo "aw_repo_url: http://50.116.42.103/ansible-tower_nightlies_RTYUIOPOIUYTYU" >> ${PLAYBOOK_DIR}/vars.yaml
        ;;
    galaxy*-false|galaxy*-no)
        echo "aw_repo_url: http://50.116.42.103/galaxy_nightlies_Y6ptm6ES82A5h79V" >> ${PLAYBOOK_DIR}/vars.yaml
        ;;
    *)
        echo "aw_repo_url: http://releases.ansible.com/${PLAYBOOK%%.yml}" >> ${PLAYBOOK_DIR}/vars.yaml
        ;;
esac

# Determine which distros to deploy
case ${CLOUD_PROVIDER}-${PLATFORM} in
    # All ec2 distros
    ec2-all)
        RAX_IMAGES="[]"
        GCE_IMAGES="[]"
        AZURE_IMAGES="[]"
        ;;
    # A specific ec2 distro
    ec2-*)
        RAX_IMAGES="[]"
        GCE_IMAGES="[]"
        AZURE_IMAGES="[]"
        # use desired ec2 distro
        EC2_IMAGES=$(filter_images ec2 ${PLATFORM})
        ;;
    # All rax distros
    rax-all)
        EC2_IMAGES="[]"
        GCE_IMAGES="[]"
        AZURE_IMAGES="[]"
        ;;
    # A specific rax distro
    rax-*)
        EC2_IMAGES="[]"
        GCE_IMAGES="[]"
        AZURE_IMAGES="[]"
        # use desired rax distro
        RAX_IMAGES=$(filter_images rax ${PLATFORM})
        ;;
    # All gce distros
    gce-all)
        EC2_IMAGES="[]"
        RAX_IMAGES="[]"
        AZURE_IMAGES="[]"
        ;;
    # A specific gce distro
    gce-*)
        EC2_IMAGES="[]"
        RAX_IMAGES="[]"
        AZURE_IMAGES="[]"
        # use desired rax distro
        GCE_IMAGES=$(filter_images gce ${PLATFORM})
        ;;
    # All azure distros
    azure-all)
        EC2_IMAGES="[]"
        RAX_IMAGES="[]"
        GCE_IMAGES="[]"
        ;;
    # A specific azure distro
    azure-*)
        EC2_IMAGES="[]"
        RAX_IMAGES="[]"
        GCE_IMAGES="[]"
        # use desired rax distro
        AZURE_IMAGES=$(filter_images azure ${PLATFORM})
        ;;
    all-all)
        # the default is all clouds, all distros ... no action required
        ;;
    all-*)
        EC2_IMAGES=$(filter_images ec2 ${PLATFORM})
        RAX_IMAGES=$(filter_images rax ${PLATFORM})
        GCE_IMAGES=$(filter_images gce ${PLATFORM})
        AZURE_IMAGES=$(filter_images azure ${PLATFORM})
        ;;
    *)
        # the default is all clouds, all distros ... no action required
        ;;
esac

# If custom distros are needed, save them in ${PLAYBOOK_DIR}/vars.yaml
if [ -n "${EC2_IMAGES}" ]; then
    echo "ec2_images: ${EC2_IMAGES}" >> ${PLAYBOOK_DIR}/vars.yaml
fi
if [ -n "${RAX_IMAGES}" ]; then
    echo "rax_images: ${RAX_IMAGES}" >> ${PLAYBOOK_DIR}/vars.yaml
fi
if [ -n "${GCE_IMAGES}" ]; then
    echo "gce_images: ${GCE_IMAGES}" >> ${PLAYBOOK_DIR}/vars.yaml
fi
if [ -n "${AZURE_IMAGES}" ]; then
    echo "azure_images: ${AZURE_IMAGES}" >> ${PLAYBOOK_DIR}/vars.yaml
fi

#
# Custom awx passwords?  If no password is provided, a random password will be
# created
#

AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD-$(gen_passwd)}
if [ -n "${AWX_ADMIN_PASSWORD}" ]; then
    echo "admin_password: ${AWX_ADMIN_PASSWORD}" >> ${PLAYBOOK_DIR}/vars.yaml
fi

AWX_PG_PASSWORD=${AWX_PG_PASSWORD-$(gen_passwd)}
if [ -n "${AWX_PG_PASSWORD}" ]; then
    echo "pg_password: ${AWX_PG_PASSWORD}" >> ${PLAYBOOK_DIR}/vars.yaml
fi

# Add custom ssh pubkeys
if [ -n "${AUTHORIZED_KEYS}" ]; then
    echo "authorized_keys: " >> ${PLAYBOOK_DIR}/vars.yaml
    echo "${AUTHORIZED_KEYS}" | while read LINE;
    do
        test -z "${LINE}" && continue
        echo  "  - '${LINE}'" >> ${PLAYBOOK_DIR}/vars.yaml
    done
fi

# Disable strict host key checking
export ANSIBLE_HOST_KEY_CHECKING=False

# How much verbosity do you want ...
if [[ "${VERBOSE}" == true ]]; then
  ARGS="-vvvv"
else
  ARGS="-v"
fi

ansible-playbook ${ARGS} -i ${PLAYBOOK_DIR}/inventory -e @${PLAYBOOK_DIR}/vars.yaml "${PLAYBOOK_PATH}"

exit $?
