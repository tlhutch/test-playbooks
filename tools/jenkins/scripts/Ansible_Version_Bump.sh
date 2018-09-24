#!/usr/bin/env bash

# Note: Git plugin sets GIT_BRANCH to branch that triggered job
# See https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin#GitPlugin-Environmentvariables
    

echo "GIT_PREVIOUS_COMMIT: ${GIT_PREVIOUS_COMMIT}"
echo "GIT_COMMIT: ${GIT_COMMIT}"

changed_files=`git diff --stat ${GIT_PREVIOUS_COMMIT}..HEAD`
if [[ $changed_files = *"lib/ansible/release"* ]]; then
  echo "VERSION changed"
else
  echo "VERSION not changed" 
fi
