#!/usr/bin/env bash

pip install -U jenkinsapi
pip install -U slacker

SKIP="false"
export SLACK_CHANNEL="#ship_it"
if [[ ${JOB_NAME} == Test_Tower_Integration ]]; then
  export MATRIX_JOB="True"
  export BUILD_LABEL="rhel-7.5-x86_64 / stable-2.6"
  export SHOW_BUTTON_OWNER="True"
elif [[ ${JOB_NAME} == Test_Tower_Integration_Patch ]]; then
  export MATRIX_JOB="True"
  export BUILD_LABEL="rhel-7.4-x86_64 / stable-2.5"
  # Only need button owner shown once in #ship_it
  export SHOW_BUTTON_OWNER="False"
  if [ $(date +%A) != Monday ]; then
     SKIP="true"
  fi
elif [[ ${JOB_NAME} == Test_Tower_Integration_Cluster ]]; then
  export MATRIX_JOB="True"
  export BUILD_LABEL=""
  export SHOW_BUTTON_OWNER="False"
else
  # Test_Tower_OpenShift_Integration
  export MATRIX_JOB="False"
  export SHOW_BUTTON_OWNER="False"
fi

if [[ $TEST_NOTIFICATION == true ]]; then
  export SLACK_CHANNEL="#test-slack"
fi

if [ ${SKIP} != true ] || [[ $TEST_NOTIFICATION == true ]]; then
  python integration_bot.py
fi
