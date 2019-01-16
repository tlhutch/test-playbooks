# Inventory Plugin Adoption

### Feature Summary

Tower 3.5 begins to take advantage of modern ansible inventory plugins
when avialable from the ansible version being used.

### Related information
* [AWX Ticket](https://github.com/ansible/awx/issues/2630)
* [ansible docs for plugins](https://docs.ansible.com/ansible/2.6/plugins/inventory.html?highlight=inventory%20plugins#plugin-list)
* [tower-qa ticket](https://github.com/ansible/tower-qa/issues/2652)

#### Upstream work
* [Work around to access dependencies in virtual env for ansible-inventory](https://github.com/ansible/ansible/issues/50714)
* [Needed Bugfix for Azure](https://github.com/ansible/ansible/pull/50006)
* [License comparision in ansible Tower inventoyr plugin is broken] **No Issue Yet**
   * Currently if there are license issues this fails and does not tell you whats up
     https://github.com/ansible/ansible/blob/devel/lib/ansible/plugins/inventory/tower.py#L126

#### Necessary pre-work

Currently inventory updates do not support use of virutal environments,
at this is necessary for dev and QE sanity, so that dependencies can be
installed and performance between versions of ansible compared on the
same install.

The virtual environment is set at the organization level and then used by any
inventory updates that populate inventories in the organization.

- [ ] Secure stable Sat6 instance with reasonable host count and add credentials to credentials.vault
- [ ] Secure stable RHV instance and add credentials to credentials.vault
- [ ] Add credentials for tower OpenStack to credentials.vault
- [ ] Add credentials for RH vSphere OpenStack to credentials.vault
- [ ] Add credentials for RH vSphere OpenStack to credentials.vault


### Test case prerequisites

- [ ] Update playbooks to work with docker to create virtual environments on the fly from test suite.

### Test suites and cases
* [ ] API
    - [ ] Able to select what virtual environment an organization uses
       - [ ] Confirm this is the virtual environment that an inventory update runs in that populates the inventory in this organization.
       - [ ] Confirm that changing the venv at the org level also changes what venv the inventory update runs in.
    - [ ] GCE
       - [ ] Confirm plugin is used in virtual environments with ansible >= X.X
       - [ ] Confirm that script is used in venvs with ansible < X.X
       - [ ] Confirm that output is sane and jobs can be run against inventory
       - [ ] Confirm plugin uses proper credentials
       - [ ] Confirm that credentials can be changed
    - [ ] Azure
       - [ ] Confirm plugin is used in virtual environments with ansible >= X.X
       - [ ] Confirm that script is used in venvs with ansible < X.X
       - [ ] Confirm that output is sane and jobs can be run against inventory
       - [ ] Confirm plugin uses proper credentials
       - [ ] Confirm that credentials can be changed
    - [ ] EC2
       - [ ] Confirm plugin is used in virtual environments with ansible >= X.X
       - [ ] Confirm that script is used in venvs with ansible < X.X
       - [ ] Confirm that output is sane and jobs can be run against inventory
       - [ ] Confirm plugin uses proper credentials
       - [ ] Confirm that credentials can be changed
    - [ ] Openstack
       - [ ] Confirm plugin is used in virtual environments with ansible >= X.X
       - [ ] Confirm that script is used in venvs with ansible < X.X
       - [ ] Confirm that output is sane and jobs can be run against inventory
       - [ ] Confirm plugin uses proper credentials
       - [ ] Confirm that credentials can be changed
    - [ ] VMWare
       - [ ] Confirm plugin is used in virtual environments with ansible >= X.X
       - [ ] Confirm that script is used in venvs with ansible < X.X
       - [ ] Confirm that output is sane and jobs can be run against inventory
       - [ ] Confirm plugin uses proper credentials
       - [ ] Confirm that credentials can be changed
    - [ ] Sat6/Foreman
       - [ ] Confirm plugin is used in virtual environments with ansible >= X.X
       - [ ] Confirm that script is used in venvs with ansible < X.X
       - [ ] Confirm that output is sane and jobs can be run against inventory
       - [ ] Confirm plugin uses proper credentials
       - [ ] Confirm that credentials can be changed
    - [ ] RHV
       - [ ] Confirm plugin is used in virtual environments with ansible >= X.X
       - [ ] Confirm that script is used in venvs with ansible < X.X
       - [ ] Confirm that output is sane and jobs can be run against inventory
       - [ ] Confirm plugin uses proper credentials
       - [ ] Confirm that credentials can be changed

* [ ] UI
		- [ ] Information is available that notifies user that the org level venv will be used for inventory updates.
    - [ ] Regression testsing (should be no user experience change in UI)


### Punting to future releases
* Openshift (plugin needs work to allow secure authentication)
* Cloudforms (no plugin)
