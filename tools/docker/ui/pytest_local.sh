#!/bin/bash -e
HOST=$1
INVENTORY=$2

#
# Determine base url
#
BASE_URL="https://$(ansible -i ${INVENTORY} --list-hosts ${HOST} | tail -n 1 | awk 'NR==1{print $1}')"

#
# Run tests
#
py.test --ansible-sudo \
        --ansible-host-pattern "${HOST}" \
        --ansible-inventory "${INVENTORY}" \
        --base-url "${BASE_URL}" \
        ${@:3}
