# Tower 3.4.4 Release Test Plan

## Overview

* 3.4.4 issues available [here](https://github.com/orgs/ansible/projects/17).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.4.3...release_3.4.4)
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.4.3...release_3.4.4)


### Verification steps

This maintenance releases contains 2 fixes:

  * A [CVE-2019-9740](https://access.redhat.com/security/cve/cve-2019-9740) fix
  * A isolated node heartbeat fix

On RHEL latest and Ubuntu latest:

  * [x] Install
  * [x] Upgrade
  * [x] Backup And Restore
  * [x] Regression

Verification links:

  * [Verification Pipeline | RHEL latest - Ansible Stable 2.8 (latest)](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1198/pipeline)
  * [Verification Pipeline | RHEL latest - Ansible Stable 2.7](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1343/pipeline)
  * [Verification Pipeline | RHEL latest - Ansible Stable 2.6](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1344/pipeline)
  * [Verification Pipeline | Ubuntu latest - Ansible Stable 2.8 (latest)](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1283/pipeline)
  * [OpenShift - Integration](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_OpenShift_Integration/504/testReport) (Failures are flakies)

