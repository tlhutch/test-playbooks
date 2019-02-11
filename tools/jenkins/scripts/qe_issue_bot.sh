#!/usr/bin/env bash
set -euxo pipefail

# Enable python3 if this version of tower-qa uses it
if [ "$(grep -s "python3" tox.ini)" ]; then
python3 -m venv $PWD/venv
source $PWD/venv/bin/activate
fi

pip install -Ur scripts/requirements.bots

if [[ $TEST_NOTIFICATION == true ]]; then
  export SLACK_CHANNEL="#test-slack"
else
  export SLACK_CHANNEL="#ship_it"
fi

python tools/bots/issue_bot.py
