#!/bin/bash -e

# Use inventory.log artifact (requires copy artifact plugin)
ANSIBLE_INVENTORY="playbooks/inventory.log"

# Determine BASEURL by finding a host in PLATFORM within the inventory file
INVENTORY_LINE=$(grep "^\[ ${PLATFORM} \]" -A1 ${ANSIBLE_INVENTORY} | tail -n1)
set -- ${INVENTORY_LINE}
BASEURL="https://$1"

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
py.test -v -m integration \
  --destructive \
  --api-debug \
  --junit-xml tests/results.xml \
  --webqareport tests/results/index.html \
  --baseurl "${BASEURL}" \
  --ansible-inventory "${ANSIBLE_INVENTORY}" \
  tests/

exit $?
