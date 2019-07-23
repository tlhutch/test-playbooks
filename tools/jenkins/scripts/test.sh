#!/usr/bin/env bash

set -euxo pipefail

TESTEXPR=${TESTEXPR:-''}
INVENTORY=${INVENTORY:-''}
TOWERKIT_BRANCH=${TOWERKIT_BRANCH:-''}
VARS_FILE=${VARS_FILE:-playbooks/vars.yml}
PYTEST_NUMPROCESSES="4"

# -- Start
#
# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common

setup_python3_env

pip install -Ur scripts/requirements.install
pip install -Ur requirements.txt

if [[ -n "${TOWERKIT_BRANCH}" ]]; then
    pip install -U "git+ssh://git@github.com/ansible/towerkit.git@${TOWERKIT_BRANCH}"
fi

echo "y" | pip uninstall pytest-mp || true

if [[ -z "${INVENTORY}" ]]; then
    INVENTORY=$(retrieve_inventory_file)
fi
TOWER_HOST=$(retrieve_tower_server_from_inventory "${INVENTORY}")
CREDS=$(retrieve_credential_file "${INVENTORY}")

set +e

# Run license tests that need to run serially
pytest -v -c config/api.cfg \
    --junit-xml=reports/junit/results-license.xml \
    --ansible-host-pattern="${TOWER_HOST}" \
    --ansible-inventory="${INVENTORY}" \
    --api-credentials="${CREDS}" \
    --github-cfg="${CREDS}" \
    --base-url="https://${TOWER_HOST}" \
    -k "${TESTEXPR}" \
    tests/license

# pytest exits with 1 when tests were collected and run but some of the
# them failed. This is when we want to give Tower some time.
if [[ $? == 1 ]]; then
    sleep 30
    pytest --cache-show "cache/lastfailed"
fi

if ! is_tower_cluster "${INVENTORY}"; then
    if [[ "${TESTEXPR}" == "test" ]]; then
        # A bigger instance is expected when running SLOWYO, because of that, bump
        # the pytest numprocesses to 16
        PYTEST_NUMPROCESSES="16"
    fi

    if [[ -n "${TESTEXPR}" ]]; then
        TESTEXPR=" and (${TESTEXPR})"
    fi

    # Let's run tests in parallel
    pytest -v -c config/api.cfg \
        --junit-xml=reports/junit/results-parallel.xml \
        --ansible-host-pattern="${TOWER_HOST}" \
        --ansible-inventory="${INVENTORY}" \
        --api-credentials="${CREDS}" \
        --github-cfg="${CREDS}" \
        --base-url="https://${TOWER_HOST}" \
        -k "not serial${TESTEXPR}" \
        -n "${PYTEST_NUMPROCESSES}" --dist=loadfile

    # pytest exits with 1 when tests were collected and run but some of the
    # them failed. This is when we want to give Tower some time.
    if [[ $? == 1 ]]; then
        sleep 120
        pytest --cache-show "cache/lastfailed"
    fi

    # Run tests that need to run serially
    pytest -v -c config/api.cfg \
        --ansible-host-pattern="${TOWER_HOST}" \
        --ansible-inventory="${INVENTORY}" \
        --api-credentials="${CREDS}" \
        --github-cfg="${CREDS}" \
        --base-url="https://${TOWER_HOST}" \
        -k "serial${TESTEXPR}"

    # pytest exits with 1 when tests were collected and run but some of the
    # them failed. This is when we want to give Tower some time.
    if [[ $? == 1 ]]; then
        sleep 120
        pytest --cache-show "cache/lastfailed"
    fi

    # Workaround https://github.com/pytest-dev/pytest-xdist/issues/445<Paste>
    ./scripts/prefix_lastfailed "$(find .pytest_cache -name lastfailed)"
    pytest --cache-show "cache/lastfailed"
else
    pytest -v -c config/api.cfg \
        --ansible-host-pattern="${TOWER_HOST}" \
        --ansible-inventory="${INVENTORY}" \
        --api-credentials="${CREDS}" \
        --github-cfg="${CREDS}" \
        --base-url="https://${TOWER_HOST}" \
        -k "${TESTEXPR}"

    # pytest exits with 1 when tests were collected and run but some of the
    # them failed. This is when we want to give Tower some time.
    if [[ $? == 1 ]]; then
        sleep 120
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
    ./scripts/merge_junit \
        reports/junit/results{-license,-parallel,,-rerun,-final}.xml
else
    ./scripts/merge_junit \
        reports/junit/results{-license,,-rerun,-final}.xml
fi

set -e
