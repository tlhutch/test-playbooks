# tower-qa tests

This document describes the process for setting up a system for running the
Ansible Tower integration test suite.

## Pre-requisites

The installation instructions assume the following software is installed.

1. [python-virtualenv](http://virtualenv.readthedocs.org)
2. [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org)
3. SSH must be installed and running on the system under test (e.g. Tower)

## Instructions

Use the following procedure to prepare your system for running the Ansible
Tower integration test suite.  The procedure must be run from the root
directory of the repository.

1. Create, and activate, a python virtual environment.

        mkvirtualenv tower-qa
        workon tower-qa

2. Install test requirements using `pip`.

        pip install -r tests/requirements.txt

3. Create a credentials file named `tests/credentials.yml` using the template `tests/credentials.template` as a guide.

        cp tests/credentials.template tests/credentials.yml

4. Update the `tests/credentials.yml` file by adding all available credentials.  For help, refer to [CREDENTIALS.md](CREDENTIALS.md).

        vim tests/credentials.yml  # update as needed

5. Determine the URL for an existing Ansible Tower instance (e.g. `https://tower.example.com`).

6. Create an [ansible inventory file](http://docs.ansible.com/intro_inventory.html) `playbooks/inventory.tower` that describes your Ansible Tower instance.

        cat <<EOF>playbooks/inventory.tower
        [ansible-tower]
        tower.example.com ansible_ssh_user=root
        EOF

7. Disable ansible host key checking

        export ANSIBLE_HOST_KEY_CHECKING=False

8. From the root directory of the repository, run all the tests with the
   following command.  Note, it's more common to limit test execution with
   either the `-m` and/or `-k` parameters.

        py.test \
            --ansible-inventory=playbooks/inventory.tower \
            --ansible-host-pattern=tower.example.com \
            --baseurl https://tower.example.com \
            --destructive \
            tests

## Recommended Reading

* [HomeBrew](http://brew.sh/) - Additional package manager for OSX.
* [Automated Test Hell](http://www.slideshare.net/wseliga/escaping-testhellxpdaysukraine2013) - presentation on automation best practices and learning experiences.
* [pytest](http://pytest.org/latest/) - The python test framework used by tower-qa.
* [pytest usage and invocations](http://pytest.org/latest/usage.html) - Learn how to run `py.test` from the command-line.
* [pytest selenium plugin](https://github.com/pytest-dev/pytest-selenium) -  The pytest selenium plugin used by browser UI automation.

## TODO

1. Model comprehensive RBAC test scenario
1. Comprehensive performance scenarios
