#!/bin/bash -e

# Use inventory.log artifact (requires copy artifact plugin)
ANSIBLE_INVENTORY="playbooks/inventory.log"

# Determine BASEURL by finding a host in PLATFORM within the inventory file
INVENTORY_LINE=$(grep "^\[ ${PLATFORM} \]" -A1 ${ANSIBLE_INVENTORY} | tail -n1)
set -- ${INVENTORY_LINE}
BASEURL="https://$1"

# Gather SCM private key credentials
if [ -z "${SCM_KEY_DATA}" ]; then
    SCM_KEY_DATA="$HOME/.ssh/id_rsa.github-ansible-jenkins-nopassphrase"
fi
if [ -z "${SCM_KEY_DATA_ENCRYPTED}" ]; then
    SCM_KEY_DATA_ENCRYPTED="$HOME/.ssh/id_rsa.github-ansible-jenkins-passphrase"
fi

# Gather SSH private key credentials
if [ -z "${SSH_KEY_DATA}" ]; then
    SSH_KEY_DATA="$HOME/.ssh/id_rsa.jenkins-nopassphrase"
fi
if [ -z "${SSH_KEY_DATA_ENCRYPTED}" ]; then
    SSH_KEY_DATA_ENCRYPTED="$HOME/.ssh/id_rsa.jenkins-passphrase"
fi

# Create and modify credentials.yaml
python scripts/create_credentials.py tests/credentials.template tests/credentials.yaml

export ANSIBLE_NOCOLOR=True
export ANSIBLE_HOST_KEY_CHECKING=False

# Run the tests ...
py.test -v -m integration \
  --destructive \
  --api-debug \
  --junit-xml tests/results.xml \
  --webqareport tests/results/index.html \
  --baseurl "${BASEURL}" \
  --ansible-inventory "${ANSIBLE_INVENTORY}" \
  tests/
