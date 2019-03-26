# Inventory Plugin Adoption

### Feature Summary

Tower 3.5 begins to take advantage of modern ansible inventory plugins
when avialable from the ansible version being used.

### Related information
* [AWX Ticket](https://github.com/ansible/awx/issues/2630)
* [ansible docs for plugins](https://docs.ansible.com/ansible/2.8/plugins/inventory.html?highlight=inventory%20plugins#plugin-list)
* [tower-qa ticket](https://github.com/ansible/tower-qa/issues/2652)

#### Upstream work
As there are many issues, they have been put into an org level project
* https://github.com/orgs/ansible/projects/6

#### Necessary pre-work

- [x] Support use of venvs for inventory updates so we can compare performance of script and plugin on same tower

### Test case prerequisites

- [x] Update towerkit to create inventories in compatibility mode
- [x] Update playbooks to work with docker to create virtual environments on the fly from test suite.

### Test suites and cases
* [ ] API
    - [x] At module scope, install custom virtual environments to run updates in.
		- [x] For each source, determine and document if the plugin output is the same, a superset, or different from the script output
          * Make custom venvs for supported versions of python, install ansible in there
          * Walk over each version and run the update, compare results
          * Outcome: [invention of compatiblity mode](https://docs.google.com/document/d/1zfSrjjDvSoAwjCQTn9T4wOrO5GVoidqGZ0XmIvqsbl4/edit#)
          * Constructing superset of script output
    - [x] Able to select what virtual environment an organization uses
       - [x] Confirm this is the virtual environment that an inventory update runs in that populates the inventory in this organization.
       - [x] Confirm that changing the venv at the org level also changes what venv the inventory update runs in.
    - [x] GCE
       - [x] Confirm plugin is used in virtual environments with ansible >= 2.8
       - [x] Confirm that script is used in venvs with ansible < 2.8
       - [x] Confirm that the inventory is populated with expected hosts
       - [x] Assert critical hostvars present in compatability mode
       - [x] Assert critical groups present in compatiblity mode
       - [x] Confirm that the inventory update creates a usable inventory (manual because we need to know we connect to machine)
           * Ansible plugins should be tested by ansible core, but we need to confirm we are not mucking with output
    - [x] Azure
       - [x] Confirm plugin is used in virtual environments with ansible >= 2.8
       - [x] Confirm that script is used in venvs with ansible < 2.8
       - [x] Confirm that the inventory is populated with expected hosts
       - [x] Assert critical hostvars present in compatability mode
       - [x] Assert critical groups present in compatiblity mode -- done via source_vars as was done in scripts
    - [ ] EC2
       - [x] Confirm plugin is used in virtual environments with ansible >= 2.8
       - [x] Confirm that script is used in venvs with ansible < 2.8
       - [x] Confirm that the inventory is populated with expected hosts
       - [x] Assert critical hostvars present in compatability mode
       - [x] Assert critical groups present in compatiblity mode
       - [ ] use AWS credential with an SCM inventory having an aws_ec2.yaml
    - [x] Tower
       - [x] Confirm plugin is used in virtual environments with ansible >= 2.8
       - [x] Confirm that script is used in venvs with ansible < 2.8
       - [x] Confirm that the inventory is populated with expected hosts
       - [x] Assert critical hostvars present in compatability mode
    - [x] Openstack
       - [x] Confirm plugin is used in virtual environments with ansible >= 2.8
       - [x] Confirm that script is used in venvs with ansible < 2.8
       - [x] Confirm that the inventory is populated with expected hosts
       - [x] Assert critical hostvars present in compatability mode
       - [x] Assert critical groups present in compatiblity mode

* [ ] UI
		- [x] Information is available that notifies user that the org level venv will be used for inventory updates. ( see https://github.com/ansible/awx/issues/3059 and https://github.com/ansible/tower/issues/2575 )
    - [ ] Regression testing
    - [x] Validate presence and operation of compatiblity mode checkbox
    - [ ] Made RFE to set venv on inventory souce because of concern for upgrade experience https://github.com/ansible/awx/issues/3387

### Punting to future releases
* RHV plugin not yet implemented in core
* Cloudforms not yet implemented in core
* Openshift requires novel approach not yet architected
* VMWare plugin use punted for this release because of time/need to test and collaborate with upstream
* Sat6/Foreman plugin use punted for this release because of time/need to test and collaborate with upstream
