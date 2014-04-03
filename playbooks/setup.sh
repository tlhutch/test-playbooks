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
# Convenience function to load images from group_vars/all
#
filter_images() {
    # $1 = [ec2,rax]
    # $2 = [all,rhel,ubuntu,centos]
    python -c "import yaml; data = yaml.load(open('group_vars/all','r')); print [i for i in data['${1}_images'] if '${2}' in i['name']]"
}

# Determine which playbook was requested
if [ $# -ne 1 ]; then
    echo "Usage: $0 <playbook>"
    exit 1
fi
PLAYBOOK=${1}

# Assert expected environment variables exist
for VARNAME in JOB_NAME JENKINS_HOME ;
do
    if [ -z "${!VARNAME}" ]; then
        echo "ERROR: variable $VARNAME undefined"
        exit 1
    fi
done

# Create json argument file
cat << EOF >vars.yaml
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
            echo "${VARNAME,,}: ${!VARNAME}" >> vars.yaml
            ;;
        AWX*|GALAXY*|AWS*|EC2*|RAX*|INSTANCE*)
            echo "${VARNAME,,}: '${!VARNAME}'" >> vars.yaml
            ;;
        *)
            echo "Ignoring environment variable: $VARNAME"
            ;;
    esac
done

# Enable nightly ansible repository?
if [[ "${ENABLE_ANSIBLE_NIGHTLY_REPO}" == true ]]; then
    echo "ansible_nightly_repo: http://50.116.42.103/ansible_nightlies_QcGXFZKv5VfQHi" >> vars.yaml
fi

# Establish the aw_repo_url.  This is the baseurl used by the install playbook.
# If OFFICIAL=yes, use the public repository. Otherwise, use the nightly
# repository.
case "${PLAYBOOK}-${OFFICIAL}" in
    awx*-false|awx*-no|ansible-tower*-false|ansible-tower*-no)
        echo "aw_repo_url: http://50.116.42.103/ansible-tower_nightlies_RTYUIOPOIUYTYU" >> vars.yaml
        ;;
    galaxy*-false|galaxy*-no)
        echo "aw_repo_url: http://50.116.42.103/galaxy_nightlies_Y6ptm6ES82A5h79V" >> vars.yaml
        ;;
    *)
        echo "aw_repo_url: http://releases.ansible.com/${PLAYBOOK%%.yml}" >> vars.yaml
        ;;
esac

# Determine which distros to deploy
case ${CLOUD_PROVIDER}-${PLATFORM} in
    # All ec2 distros
    ec2-all)
        # disable rax
        RAX_IMAGES="[]"
        ;;
    # A specific ec2 distro
    ec2-*)
        # disable rax
        RAX_IMAGES="[]"
        # use desired ec2 distro
        EC2_IMAGES=$(filter_images ec2 ${PLATFORM})
        ;;
    # All rax distros
    rax-all)
        # disable ec2
        EC2_IMAGES="[]" #
        ;;
    # A specific rax distro
    rax-*)
        # disable ec2
        EC2_IMAGES="[]"
        # use desired rax distro
        RAX_IMAGES=$(filter_images rax ${PLATFORM})
        ;;
    all-all)
        # the default is all clouds, all distros ... no action required
        ;;
    all-*)
        # use desired ec2 distro
        EC2_IMAGES=$(filter_images ec2 ${PLATFORM})
        # use desired rax distro
        RAX_IMAGES=$(filter_images rax ${PLATFORM})
        ;;
    *)
        # the default is all clouds, all distros ... no action required
        ;;
esac

# If custom distros are needed, save them in vars.yaml
if [ -n "${RAX_IMAGES}" ]; then
    echo "rax_images: ${RAX_IMAGES}" >> vars.yaml
fi
if [ -n "${EC2_IMAGES}" ]; then
    echo "ec2_images: ${EC2_IMAGES}" >> vars.yaml
fi

#
# Custom awx passwords?  If no password is provided, a random password will be
# created
#

AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD-$(gen_passwd)}
if [ -n "${AWX_ADMIN_PASSWORD}" ]; then
    echo "admin_password: ${AWX_ADMIN_PASSWORD}" >> vars.yaml
fi

AWX_PG_PASSWORD=${AWX_PG_PASSWORD-$(gen_passwd)}
if [ -n "${AWX_PG_PASSWORD}" ]; then
    echo "pg_password: ${AWX_PG_PASSWORD}" >> vars.yaml
fi

# Add custom ssh pubkeys
if [ -n "${AUTHORIZED_KEYS}" ]; then
    echo "authorized_keys: " >> vars.yaml
    echo "${AUTHORIZED_KEYS}" | while read LINE;
    do
        test -z "${LINE}" && continue
        echo  "  - '${LINE}'" >> vars.yaml
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

ansible-playbook ${ARGS} -i inventory -e @vars.yaml "${PLAYBOOK}"
