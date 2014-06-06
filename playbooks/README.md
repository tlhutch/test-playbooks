ansibleworks-qa playbooks
=========================

[Ansible](http://ansible.cc/) playbook/roles for deploying a Ansible Tower and
related services.

## ansibleworks-qa repository/structure

 * files - files and templates for use in playbooks/tasks
 * group_vars - customize deployment by setting/replacing variables
 * handlers - common service handlers
 * library - library of custom local ansible modules
 * tasks - snippets of tasks that should be included in plays

## Dependencies
 * [ansible](https://github.com/ansible/ansible)

## Instructions
1. Clone this repo

        git clone https://github.com/ansible/ansibleworks-qa.git

2. Run the playbook:

        ansible-playbook -i inventory site.yml

Please send me feedback by way of github issues.  Pull requests encouraged!
