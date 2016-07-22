#!/bin/bash -xe

INVENTORY=$1
HOST=$2
PLATFORM=$3
BROWSER=$4
PYTEST_MARK_EXPR=$5
PYTEST_TEST_EXPR=$6

#
# Example:
#
# EXPORT SAUCELABS_USERNAME=jakemcdermott
# EXPORT SAUCELABS_API_KEY=gjeV4XcHhiaEzqMKeL6L4wjkN2MaOX
# ./scripts/jenkins_sauce.sh playbooks/inventory.log primary linux Chrome "ui" "pagination"
#

#
# Determine base url
#
BASE_URL="https://$(ansible -i ${INVENTORY} --list-hosts ${HOST} | tail -n 1 | awk 'NR==1{print $1}')"

#
# Run tests
#

py.test \
    --supported-window-sizes 'maximized,800x600' \
    --ansible-sudo \
    --ansible-host-pattern "${HOST}" \
    --ansible-inventory "${INVENTORY}" \
    --base-url "${BASE_URL}" \
    --capability platform "${PLATFORM}" \
    --capability browserName "${BROWSER}" \
    --capability recordScreenshots false \
    --capability videoUploadOnPass false \
    --driver SauceLabs \
    --html ./results/report.html \
    --force-flaky \
    --max-runs 3 \
    --min-passes 1 \
    -m "${PYTEST_MARK_EXPR}" \
    -k "${PYTEST_TEST_EXPR}" \
    tests/ui
