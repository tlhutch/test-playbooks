#!/usr/bin/env bash

set -euxo pipefail

if [[ -z "${OPENSHIFT_TOKEN}" ]]; then
    >&2 echo "openshift_install.sh: Environment variable OPENSHIFT_TOKEN must be specified"
    exit 1
fi

if [[ -z "${OPENSHIFT_PROJECT}" ]]; then
    >&2 echo "openshift_install.sh: Environment variable OPENSHIFT_PROJECT must be specified"
    exit 1
fi

if [[ "${OPENSHIFT_PROJECT}" == 'tower-qe' ]] || [[ "${OPENSHIFT_PROJECT}" == 'tower' ]]; then
    >&2 echo "openshift_install.sh: OpenShift project 'tower' and 'tower-qe' are protected"
    exit 1
fi

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env

openshift_login
oc -n "${OPENSHIFT_PROJECT}" delete pods --all --grace-period=0 --force
oc delete project "${OPENSHIFT_PROJECT}" --grace-period=0 --force
