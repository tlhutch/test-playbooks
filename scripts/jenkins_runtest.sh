#!/bin/bash -xe
#
# Usage: jenkins_runtest.sh [MARKEXPR]
#
# Where [MARKEXPR] defaults to "not (performance or ui or ldap or ha)"
#
# The following environment variables are recognized:
#
#    TESTEXPR - value passed to py.test -m <TESTEXPR>
#    JUNIT_XML - value passed to py.test --junit-xml
#    HTML_REPORT - value passed to py.test --html
#    ANSIBLE_INVENTORY - path to ansible inventory file (default: playbooks/inventory.log)

# Variable defaults
MARKEXPR=${@:-not (performance or ui or ldap or ha)}
TESTEXPR=${TESTEXPR:-}
ANSIBLE_INVENTORY=${ANSIBLE_INVENTORY:-playbooks/inventory.log}
ANSIBLE_VERSION=$(python -c 'import ansible; print ansible.__version__;')
JUNIT_XML=${JUNIT_XML:-tests/results.xml}
HTML_REPORT=${HTML_REPORT:-tests/results/index.html}

# Determine --base-url parameter using `ansible --list-hosts`
if [ -f "${ANSIBLE_INVENTORY}" ]; then
    INVENTORY_HOST=$(ansible "${PLATFORM}:&${CLOUD_PROVIDER}" -i ${ANSIBLE_INVENTORY} --list-hosts)
    if [ $? -ne 0 ] || [ "${INVENTORY_HOST}" == *"provided host list is empty"* ]; then
        echo "Unable to find a matching host: ${PLATFORM}:&${CLOUD_PROVIDER}"
        exit 1
    fi
    IFSBAK="${IFS}" IFS=$'\n'
    INVENTORY_HOST_ARRAY=(${INVENTORY_HOST})            # Parse lines into array
    if [[ "${ANSIBLE_VERSION}" = 2* ]]; then            #Ansible v2 includes summary line (remove if present)
        INVENTORY_HOST_ARRAY=("${INVENTORY_HOST_ARRAY[@]:1}")
    fi
    if [ ${#INVENTORY_HOST_ARRAY[@]} -ne 1 ]; then      # Confirm one host listed 
        echo "Host list does not contain exactly one host"
        exit 1
    fi
    INVENTORY_HOST="${INVENTORY_HOST_ARRAY[0]}"
    INVENTORY_HOST="${INVENTORY_HOST//[[:space:]]/}"    # remove whitespace
    IFS="${IFSBAK}"
else
    echo "Ansible inventory file not found: ${ANSIBLE_INVENTORY}"
    exit 1
fi

export ANSIBLE_NOCOLOR=True
export ANSIBLE_HOST_KEY_CHECKING=False

# Initialize arguments
PY_ARGS=(-m "${MARKEXPR}")
PY_ARGS+=(-k "${TESTEXPR}")
PY_ARGS+=(--junit-xml "${JUNIT_XML}")
PY_ARGS+=(--html "${HTML_REPORT}")
PY_ARGS+=(--ansible-inventory=${ANSIBLE_INVENTORY})
PY_ARGS+=(--ansible-host-pattern=${INVENTORY_HOST})
PY_ARGS+=(--ansible-sudo)
PY_ARGS+=(--base-url "https://${INVENTORY_HOST}")
PY_ARGS+=(--api-debug)
PY_ARGS+=(--api-destructive)

# Run the tests ...
py.test -v \
  "${PY_ARGS[@]}" \
  tests/

exit $?
