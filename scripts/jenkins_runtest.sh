#!/bin/bash -xe
#
# Usage: jenkins_runtest.sh [MARKEXPR]
#
# Where [MARKEXPR] defaults to "not (performance or selenium)"
#
# The following environment variables are recognized:
#
#    TESTEXPR - value passed to py.test -m <TESTEXPR>
#    JUNIT_XML - value passed to py.test --junit-xml
#    WEBQA_REPORT - value passed to py.test --webqareport
#    ANSIBLE_INVENTORY - path to ansible inventory file (default: playbooks/inventory.log)
#    SAUCE_CREDS - Saucelabs credentials file (default: tests/saucelabs.yml)
#    SAUCE_USER_NAME - Saucelabs username
#    SAUCE_API_KEY - Saucelabs API key
#    SELENIUM_DRIVER - value passed to py.test --driver
#    SELENIUM_PLATFORM - value passed to py.test --platform
#    SELENIUM_BROWSER - value passed to py.test --browsername
#    SELENIUM_VERSION - value passed to py.test --browserver
#

# Variable defaults
MARKEXPR=${@:-not (performance or selenium or ldap)}
TESTEXPR=${TESTEXPR:-}
ANSIBLE_INVENTORY=${ANSIBLE_INVENTORY:-playbooks/inventory.log}
JUNIT_XML=${JUNIT_XML:-tests/results.xml}
WEBQA_REPORT=${WEBQA_REPORT:-tests/results/index.html}
SAUCE_CREDS=${SAUCE_CREDS:-tests/saucelabs.yml}

# Determine --baseurl parameter using `ansible --list-hosts`
if [ -f "${ANSIBLE_INVENTORY}" ]; then
    INVENTORY_HOST=$(ansible "${PLATFORM}:&${CLOUD_PROVIDER}" -i ${ANSIBLE_INVENTORY} --list-hosts)
    if [ $? -ne 0 -o "${INVENTORY_HOST}" = "No hosts matched" ]; then
        echo "Unable to find a matching host: ${PLATFORM}:&${CLOUD_PROVIDER}"
        exit 1
    fi
    INVENTORY_HOST="${INVENTORY_HOST//[[:space:]]/}"    # remove whitespace
else
    echo "Ansible inventory file not found: ${ANSIBLE_INVENTORY}"
    exit 1
fi

# Create and modify credentials.yml
SCRIPT_NAME="create_credentials.py"
# Look for script in multple locations (this allows for backwards compat with
# jenkins)
for SCRIPT_DIR in "scripts" "." ; do
    if [ -f "${SCRIPT_DIR}/${SCRIPT_NAME}" ]; then
        break
    fi
done
python ${SCRIPT_DIR}/${SCRIPT_NAME} tests/credentials.template tests/credentials.yml

# Create saucelabs credentials file
if [ -n "${SAUCE_USER_NAME}" -a -n "${SAUCE_API_KEY}" ]; then
    cat << EOF > ${SAUCE_CREDS}
username: ${SAUCE_USER_NAME}
api-key: ${SAUCE_API_KEY}
EOF
    # When sauce credentials are provided, let's also pass along the SELENIUM
    # environment variables
    SAUCE_ARGS=(--saucelabs "${SAUCE_CREDS}")
    SAUCE_ARGS+=(--driver "${SELENIUM_DRIVER}")
    SAUCE_ARGS+=(--platform "${SELENIUM_PLATFORM}")
    SAUCE_ARGS+=(--browsername "${SELENIUM_BROWSER}")
    SAUCE_ARGS+=(--browserver "${SELENIUM_VERSION}")
fi

export ANSIBLE_NOCOLOR=True
export ANSIBLE_HOST_KEY_CHECKING=False

# Initialize arguments
PY_ARGS=(-m "${MARKEXPR}")
PY_ARGS+=(-k "${TESTEXPR}")
PY_ARGS+=(--junit-xml "${JUNIT_XML}")
PY_ARGS+=(--webqareport "${WEBQA_REPORT}")
PY_ARGS+=(--ansible-inventory=${ANSIBLE_INVENTORY})
PY_ARGS+=(--ansible-host-pattern=${INVENTORY_HOST})
PY_ARGS+=(--ansible-sudo)
PY_ARGS+=(--baseurl "https://${INVENTORY_HOST}")
PY_ARGS+=(--api-debug)
PY_ARGS+=(--destructive)

# Run the tests ...
py.test -v \
  "${PY_ARGS[@]}" \
  "${SAUCE_ARGS[@]}" \
  tests/

exit $?
