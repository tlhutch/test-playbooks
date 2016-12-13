#!/bin/bash

#
# This is a starter script that runs the ui tests locally using a live browser. Use it
# for debugging, writing new tests, or any other occasion where you'd like to actually
# see what is going on.
#
# example: 
#    ansible-vault decrypt --vault-password-file="${VAULT_FILE}" tools/docker/ui/credentials.yml
#    ./scripts/local_ui.sh "http://ec2-12-345-67-89.compute-1.amazonaws.com"
#

BASE_URL=$1

function error
{
    echo "${1:-"error"}" 1>&2
    exit 1
}

function get_driver
{
   local driver_base_url='https://chromedriver.storage.googleapis.com'
   local driver_version=$(curl ${driver_base_url}/LATEST_RELEASE)

   if [[ "$OSTYPE" == "linux-gnu" ]]; then
      local driver_url=${driver_base_url}/${driver_version}/chromedriver_linux64.zip
   elif [[ "$OSTYPE" == "darwin"* ]]; then
      local driver_url=${driver_base_url}/${driver_version}/chromedriver_mac64.zip
   else
      error "This script is for mac64 or linux64"
   fi
   
   curl ${driver_url} | tar zxv
}


if [ ! -f ./chromedriver ]; then
    get_driver
fi

py.test \
    --ansible-host-pattern=all \
    --ansible-inventory=playbooks/inventory \
    --api-credentials=tools/docker/ui/credentials.yml \
    --api-destructive \
    --base-url="${BASE_URL}" \
    --browser=chrome \
    --driver-type=local \
    --driver-location=./chromedriver \
    --github-cfg=tools/docker/ui/credentials.yml \
    --no-print-logs \
    tests/ui
