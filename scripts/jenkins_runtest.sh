#!/bin/bash -e

# Establish the MARKEXPR py.test parameter
MARKEXPR=${@:-not (performance or selenium)}

# Use inventory.log artifact (requires copy artifact plugin)
ANSIBLE_INVENTORY="playbooks/inventory.log"

JUNIT_XML=${JUNIT_XML:-tests/results.xml}
WEBQA_REPORT=${WEBQA_REPORT:-tests/results/index.html}

# Determine BASEURL using 'ansible --list-hosts'
INVENTORY_HOST=$(ansible "${PLATFORM}:&${CLOUD_PROVIDER}" -i ${ANSIBLE_INVENTORY} --list-hosts)
if [ $? -ne 0 -o ${INVENTORY_HOST} = "No hosts matched" ]; then
    echo "Unable to find a matching host: ${PLATFORM}:&${CLOUD_PROVIDER}"
    exit 1
fi
INVENTORY_HOST="${INVENTORY_HOST%%[![:space:]]*}"   # remove leading whitespace characters
INVENTORY_HOST="${INVENTORY_HOST##*[![:space:]]}"   # remove trailing whitespace characters

BASEURL="https://${INVENTORY_HOST}"

# Create and modify credentials.yaml
SCRIPT_NAME="create_credentials.py"
# Look for script in multple locations (this allows for backwards compat with
# jenkins)
for SCRIPT_DIR in "scripts" "." ; do
    if [ -f "${SCRIPT_DIR}/${SCRIPT_NAME}" ]; then
        break
    fi
done
python ${SCRIPT_DIR}/${SCRIPT_NAME} tests/credentials.template tests/credentials.yaml

export ANSIBLE_NOCOLOR=True
export ANSIBLE_HOST_KEY_CHECKING=False

# Run the tests ...
py.test -v \
  --api-debug \
  --junit-xml "${JUNIT_XML}" \
  --webqareport "${WEBQA_REPORT}" \
  --baseurl "${BASEURL}" \
  --ansible-inventory "${ANSIBLE_INVENTORY}" \
  -m "${MARKEXPR}" \
  --destructive \
  tests/

exit $?
