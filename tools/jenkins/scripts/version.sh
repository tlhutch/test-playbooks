#!/usr/bin/env bash

set -euo pipefail

echo "Ansible Version: $(ansible --version)" | tee version.log
echo "ansible/tower-qa version: $(git describe --tags)" | tee -a version.log
echo "ansible/towerkit version: $(pip freeze | grep 'towerkit')" | tee -a version.log
