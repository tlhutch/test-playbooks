# tower-qa tests

This document describes the process for setting up a system for running the
Ansible Tower integration test suite.

## Pre-requisites

The installation instructions assume the following software is installed.

1. [python-virtualenv](http://virtualenv.readthedocs.org)
2. [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org)

## Instructions

Use the following procedure to prepare your system for running the Ansible
Tower integration test suite.  The procedure must be run from the root
directory of the repository.

1. Create, and activate, a python virtual environment.

        mkvirtualenv tower-qa
        workon tower-qa

2. Install test requirements using `pip`.

        pip install -r tests/requirements.txt

3. Create, and modify, the file `tests/credentials.yml`.

        cp tests/credentials.template tests/credentials.yml
        vim tests/credentials.yml  # update as needed

4. Determine URL for an existing Ansible Tower instance (e.g. `http://tower.example.com`).

5. Create an [ansible inventory file](http://docs.ansible.com/intro_inventory.html) `playbooks/inventory.tower` that describes your Ansible Tower instance.

        cat <<EOF>playbooks/inventory.tower
        [ansible-tower]
        tower.example.com ansible_ssh_user=root
        EOF

6. Disable ansible host key checking

        export ANSIBLE_HOST_KEY_CHECKING=False

7. From the root directory of the repository, run all the tests with the
   following command.  Note, it's more common to limit test execution with
   either the `-m` and/or `-k` parameters.

        py.test --ansible-inventory=playbooks/inventory.tower --baseurl https://tower.example.com --destructive tests/

## Recommended Reading

* [HomeBrew](http://brew.sh/) - Additional package manager for OSX.
* [Automated Test Hell](http://www.slideshare.net/wseliga/escaping-testhellxpdaysukraine2013) - presentation on automation best practices and learning experiences.
* [pytest](http://pytest.org/latest/) - The python test framework used by tower-qa.
* [pytest usage and invocations](http://pytest.org/latest/usage.html) - Learn how to run `py.test` from the command-line.
* [pytest MozwebQA plugin](https://github.com/mozilla/pytest-mozwebqa) -  The pytest selenium plugin used by browser UI auotmation.

## TODO

1. Model comprehensive RBAC test scenario
1. Comprehensive performance scenarios
