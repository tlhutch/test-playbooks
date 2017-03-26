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

DEFAULT_INVENTORY_GROUP="${PLATFORM}:&${CLOUD_PROVIDER}"
INVENTORY_GROUP=${INVENTORY_GROUP:-$DEFAULT_INVENTORY_GROUP}
INVENTORY_HOST=$(ansible -i ${ANSIBLE_INVENTORY} --list-hosts ${INVENTORY_GROUP} | tail -n 1 | awk 'NR==1{print $1}')

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
