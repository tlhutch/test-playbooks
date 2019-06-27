#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-''}
INVENTORY=${INVENTORY:-''}
VARS_FILE=${VARS_FILE:-playbooks/vars.yml}

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env

pip install -Ur scripts/requirements.install
pip install -Ur requirements.txt

echo "y" | pip uninstall pytest-mp || true

if [[ -z "${INVENTORY}" ]]; then
    INVENTORY=$(retrieve_inventory_file)
fi
TOWER_HOST=$(retrieve_tower_server_from_inventory "${INVENTORY}")
CREDS=$(retrieve_credential_file "${INVENTORY}")

set +e

if ! is_tower_cluster "${INVENTORY}"; then
    # Run license tests that need to run serially
    if ! pytest -v -c config/api.cfg \
        --junit-xml=reports/junit/results-license.xml \
        --ansible-host-pattern="${TOWER_HOST}" \
        --ansible-inventory="${INVENTORY}" \
        --api-credentials="${CREDS}" \
        --github-cfg="${CREDS}" \
        --base-url="https://${TOWER_HOST}" \
        -k "(${TESTEXPR})"
        tests/license
    then
        sleep 300
        pytest --cache-show "cache/lastfailed"
    fi

# Let's run tests in parallel
    if ! pytest -v -c config/api.cfg \
        --junit-xml=reports/junit/results-parallel.xml \
        --ansible-host-pattern="${TOWER_HOST}" \
        --ansible-inventory="${INVENTORY}" \
        --api-credentials="${CREDS}" \
        --github-cfg="${CREDS}" \
        --base-url="https://${TOWER_HOST}" \
        -k "not serial${TESTEXPR}" \
        -n 4 --dist=loadfile
    then
        sleep 300
        pytest --cache-show "cache/lastfailed"
    fi

    # Run tests that need to run serially
    if ! pytest -v -c config/api.cfg \
        --ansible-host-pattern="${TOWER_HOST}" \
        --ansible-inventory="${INVENTORY}" \
        --api-credentials="${CREDS}" \
        --github-cfg="${CREDS}" \
        --base-url="https://${TOWER_HOST}" \
        -k "serial${TESTEXPR}"
    then
        sleep 300
        pytest --cache-show "cache/lastfailed"
    fi

    # Workaround https://github.com/pytest-dev/pytest-xdist/issues/445<Paste>
    ./scripts/prefix_lastfailed "$(find .pytest_cache -name lastfailed)"
    pytest --cache-show "cache/lastfailed"
else
    if ! pytest -v -c config/api.cfg \
        --ansible-host-pattern="${TOWER_HOST}" \
        --ansible-inventory="${INVENTORY}" \
        --api-credentials="${CREDS}" \
        --github-cfg="${CREDS}" \
        --base-url="https://${TOWER_HOST}" \
        -k "${TESTEXPR}"
    then
        sleep 300
        pytest --cache-show "cache/lastfailed"
    fi

fi

pytest -v -c config/api.cfg \
    --last-failed --last-failed-no-failures none \
    --junit-xml=reports/junit/results-rerun.xml \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    --base-url="https://${TOWER_HOST}"

if [[ -f reports/junit/results-parallel.xml ]]; then
    if [[ -f reports/junit/results-license.xml ]]; then
        ./scripts/merge_junit \
            reports/junit/results-parallel.xml \
            reports/junit/results-license.xml \
            reports/junit/results{,-rerun,-final}.xml
    else
        ./scripts/merge_junit \
            reports/junit/results-parallel.xml \
            reports/junit/results{,-rerun,-final}.xml
else
    ./scripts/merge_junit \
        reports/junit/results{,-rerun,-final}.xml
fi

set -e
