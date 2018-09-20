[![Requirements Status](https://requires.io/github/ansible/tower-qa/requirements.svg?branch=master)](https://requires.io/github/ansible/tower-qa/requirements/?branch=master)

# tower-qa

Welcome to the `tower-qa` repository.  Here you'll find playbooks, scripts, documentation and tests used for deploying and testing Ansible Tower.

## Repository structure

* `playbooks/` - ansible playbooks used for deploying tower
* `scripts/` - helper scripts
* `tests/` - tower-qa automated tests
* `docs/` - tower-qa documentation

## Git Subtree

The `tower-qa` repository uses [git subtree](https://blogs.atlassian.com/2013/05/alternatives-to-git-submodule-git-subtree/) for managing external repository dependencies.  The `tower-qa` repository currently uses the following subtree modules.

* bennojoy.openldap_server - https://github.com/bennojoy/openldap_server.git (push)
* chrismeyersfsu.iptables - [git@github.com:chrismeyersfsu/role-iptables.git](https://github.com/chrismeyersfsu/role-iptables) (fetch)
* chrismeyersfsu.required_vars - [git@github.com:chrismeyersfsu/role-required_vars.git](https://github.com/chrismeyersfsu/role-required_vars) (push)
* jlaska.ntp - [git@github.com:jlaska/ntp.git](https://github.com/jlaska/ntp) (push)
* jladdjr.inspircd - [git@github.com:jladdjr/inspircd.git](https://github.com/jladdjr/inspircd)
* jladdjr.tacacs_plus - [git@github.com:jladdjr/tacacs_plus.git](https://github.com/jladdjr/tacacs_plus)

Consult git subtree [documentation](https://blogs.atlassian.com/2013/05/alternatives-to-git-submodule-git-subtree/) for guidance on usage.  However, some examples are included below:

To add a new subtree called `chrismeyersfsu.iptables` ...

    git remote add chrismeyersfsu.iptables git@github.com:chrismeyersfsu/role-iptables.git
    git subtree add --squash --prefix playbooks/roles/chrismeyersfsu.iptables chrismeyersfsu.iptables master

To update an existing subtree called `chrismeyersfsu.iptables` ...

    git fetch chrismeyersfsu.iptables
    git subtree pull --squash --prefix playbooks/roles/chrismeyersfsu.iptables chrismeyersfsu.iptables master

To contribute back to a subtree module, first fork the repository.  In the following example, the forked repository is called `jlaska.iptables`.

    git remote add jlaska.iptables git@github.com:jlaska/role-iptables.git
    git subtree push --prefix=roles/playbooks/chrismeyersfsu.iptables jlaska.iptables master
