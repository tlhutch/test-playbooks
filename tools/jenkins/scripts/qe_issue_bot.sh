#!/usr/bin/env bash
set -euxo pipefail

# shellcheck source=lib/common
source "$(dirname "${0}")"/lib/common
setup_python3_env

pip install -Ur scripts/requirements.bots

if [[ $TEST_NOTIFICATION == true ]]; then
  export SLACK_CHANNEL="#test-slack"
else
  export SLACK_CHANNEL="#ship_it"
fi

python tools/bots/issue_bot.py
