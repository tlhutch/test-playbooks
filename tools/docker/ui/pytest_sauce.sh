#!/bin/bash -xe

INVENTORY=$1
HOST=$2
PLATFORM=$3
BROWSER=$4

#
# Example:
#
# export SAUCELABS_USERNAME=jakemcdermott
# export SAUCELABS_API_KEY=gjeV4XcHhiaEzqMKeL6L4wjkN2MaOX
# export PYTEST_ADDOPTS='-m ui -k not test_pagination'
# ./pytest_sauce.sh playbooks/inventory.log primary mac chrome
#

#
# Determine base url
#
BASE_URL="https://$(ansible -i ${INVENTORY} --list-hosts ${HOST} | tail -n 1 | awk 'NR==1{print $1}')"

#
# Run tests
#
py.test \
    --ansible-sudo \
    --ansible-host-pattern "${HOST}" \
    --ansible-inventory "${INVENTORY}" \
    --base-url "${BASE_URL}" \
    --capability platform "${PLATFORM}" \
    --capability browserName "${BROWSER}" \
    --driver SauceLabs \
    tests/ui
