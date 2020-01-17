#!/usr/bin/env bash

set -euxo pipefail

sourcefile="${BASH_SOURCE[0]}"

dirname="$(dirname $sourcefile)"

# Setup the venvs and collection for the collection tests
ansible-playbook -v -i "$dirname/../playbooks/inventory_docker" -l 'tower' -e "use_become=false ansible_user=0 venv_base=/venv venv_folder_name=python3_tower_modules remote_python=python36 venv_packages='ansible-tower-cli psutil git+https://github.com/ansible/ansible.git'" "$dirname/../playbooks/create_custom_virtualenv.yml"

set -e
