# Tower modules as AWX Collection

## Summary

This feature moves the ansible tower modules out of ansible core and into
a collection called awx collection and automation hub.
In order to do this we must put the module in
the right location and perform some basic testing on them to ensure they work
as expected.

## API Tests

- [ ] Move tower modules into an Ansible Collection that can be downloaded from
  Galaxy (https://github.com/ansible/awx/pull/4701)
- [ ] Update YOLO/SLOWYO to run awx collection tests by installing awx
  collection from galaxy, automation hub, or from git
- [ ] Augment the test coverage (tests/api/test\_tower\_modules.py) for the Tower
  modules by running the modules and checking if the entities were
  created/deleted on Tower. The subtasks track testing the create/delete
  functionality of each available module:
  - [x] credential
  - [x] credential\_type
  - [x] group
  - [x] host
  - [x] inventory
  - [ ] inventory\_source
  - [x] job\_cancel
  - [x] job\_launch
  - [x] job\_list
  - [x] job\_template
  - [x] job\_wait
  - [x] label
  - [ ] notification
  - [x] organization
  - [x] project
  - [ ] receive
  - [x] role
  - [ ] send
  - [ ] settings
  - [x] team
  - [x] user
  - [ ] workflow\_launch
  - [ ] workflow\_template
