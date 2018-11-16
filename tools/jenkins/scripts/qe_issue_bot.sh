#!/usr/bin/env bash
set -euxo pipefail

pip install -U slacker
pip install -U pygithub


if [[ $TEST_NOTIFICATION == true ]]; then
  export SLACK_CHANNEL="#test-slack"
else
  export SLACK_CHANNEL="#ship_it"
fi

python tools/bots/issue_bot.py
