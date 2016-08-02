#!/bin/bash -xe

INVENTORY=$1
HOST=$2
PLATFORM=$3
BROWSER=$4

#
# Determine base url
#
BASE_URL="https://$(ansible -i ${INVENTORY} --list-hosts ${HOST} | tail -n 1 | awk 'NR==1{print $1}')"

#
# Run tests
#
py.test \
    --ansible-host-pattern "${HOST}" \
    --ansible-inventory "${INVENTORY}" \
    --ansible-sudo \
    --base-url "${BASE_URL}" \
    --capability platform "${PLATFORM}" \
    --capability browserName "${BROWSER}" \
    --capability idleTimeout 240 \
    --driver SauceLabs \
    ${@:5}
