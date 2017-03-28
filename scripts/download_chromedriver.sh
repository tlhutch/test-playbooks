#!/usr/bin/env bash
set -e
set -u
set -o pipefail


function error
{
    echo "${1:-"error"}" 1>&2
    exit 1
}

function download_driver
{
    local driver_base_url='https://chromedriver.storage.googleapis.com'
    local driver_version=$(curl -s ${driver_base_url}/LATEST_RELEASE)

    if [[ "$OSTYPE" == "linux-gnu" ]]; then
        local driver_url=${driver_base_url}/${driver_version}/chromedriver_linux64.zip
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        local driver_url=${driver_base_url}/${driver_version}/chromedriver_mac64.zip
    else
        error "This script is for mac64 or linux64"
    fi

    curl -s ${driver_url} | tar zxv
}

if [ ! -f ./chromedriver ]; then
    download_driver
fi
