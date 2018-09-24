#!/usr/bin/env bash

# Clean-up old trigger files
rm -f *.cfg 

# Note: Git plugin sets GIT_BRANCH to branch that triggered job
# See https://wiki.jenkins-ci.org/display/JENKINS/Git+Plugin#GitPlugin-Environmentvariables

# If the branch that changed is listed as one that we should build..
touch tower-install.cfg
if [[ "${GIT_TESTED_BRANCHES}" == *${GIT_BRANCH}* ]]; then
    echo "Triggering builds for ${GIT_BRANCH}"
    echo -e "OFFICIAL=no\nGIT_BRANCH=${GIT_BRANCH}" > "nightly.cfg"
    
    #ANSIBLE_BRANCH_VERSION=$(echo ${GIT_BRANCH} | sed "s/stable-//")
    RELATIVE_GIT_BRANCH=$(echo ${GIT_BRANCH} | sed 's/^.*\/\([^\/]*\)$/\1/g')
    export ANSIBLE_STABLE_BRANCH=${RELATIVE_GIT_BRANCH}
    echo -e "ANSIBLE_STABLE_BRANCH=${RELATIVE_GIT_BRANCH}" > "tower-install.cfg"
fi
