# FIPS Compliance Test Plan


## Feature Summary

Starting from version 3.4.0 Ansible Tower should be fips-compliant, and hence be fully functionnal on a fips-enabled node.

Some external dependencies may not be fips-compliant. Those dependencies should be listed and be part of the documentation.

This document attempts to overview the automated testing requirements for the verification and final validation of this new feature.


## Related information

  * [Feature request](https://github.com/ansible/tower/issues/644)
  * [Ansible FIPS roles](https://github.com/Spredzy/ansible-role-fips)


## Test suites and cases

  * [ ] prepare/acquire FIPS-enabled RHEL-7.5 nodes - make it permanent in Jenkins
  * [ ] Integration test should pass on a FIPS-enabled RHEL-7.5 node
  * [ ] Integration test should pass on a FIPS-enabled RHEL-7.4 node
