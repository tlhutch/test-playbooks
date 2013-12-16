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
    # $1 = [aws,rax]
    # $2 = [all,rhel,ubuntu,centos]
    python -c "import yaml; data = yaml.load(open('roles/create_${1}/defaults/main.yml','r')); print [i for i in data['${1}_images'] if '${2}' in i['name']]"
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

# Append variables to argument file
for VARNAME in AW_REPO_URL \
               AWX_SETUP_PATH \
               DELETE_ON_START \
               RAX_USERNAME \
               RAX_API_KEY \
               RAX_NAME_PREFIX \
               AWS_ACCESS_KEY \
               AWS_SECRET_KEY \
               AWS_NAME_PREFIX ;
do
    # If defined, set the value in vars.yaml
    if [ -n "${!VARNAME}" ]; then
        echo "${VARNAME,,}: '${!VARNAME}'" >> vars.yaml
    fi
done

# Enable nightly ansible repository?
if [[ "${ENABLE_ANSIBLE_NIGHTLY_REPO}" == true ]]; then
    echo "ansible_repo_url: http://50.116.42.103/ansible_nightlies_QcGXFZKv5VfQHi" >> vars.yaml
fi

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
        # use desired aws distro
        AWS_IMAGES=$(filter_images aws ${PLATFORM})
        ;;
    # All rax distros
    rax-all)
        # disable aws
        AWS_IMAGES="[]" #
        ;;
    # A specific rax distro
    rax-*)
        # disable aws
        AWS_IMAGES="[]"
        # use desired rax distro
        RAX_IMAGES=$(filter_images rax ${PLATFORM})
        ;;
    all-all)
        # the default is all clouds, all distros ... no action required
        ;;
    all-*)
        # use desired aws distro
        AWS_IMAGES=$(filter_images aws ${PLATFORM})
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
if [ -n "${AWS_IMAGES}" ]; then
    echo "aws_images: ${AWS_IMAGES}" >> vars.yaml
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

# Enable verbosity?
if [[ "${VERBOSE}" == true ]]; then
  ARGS="-vvvv"
fi

ansible-playbook ${ARGS} -i inventory -e @vars.yaml "${PLAYBOOK}"
