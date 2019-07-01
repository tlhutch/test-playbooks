# Tower 3.3.6 Release Test Plan

## Overview

* 3.3.6 issues available [here](https://github.com/orgs/ansible/projects/16).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.3.5...release_3.3.6)
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.3.5...release_3.3.6)


### Verification steps

This is a CVE-related maintenance release [CVE-2019-9740](https://access.redhat.com/security/cve/cve-2019-9740)

On RHEL latest and Ubuntu latest:

  * [x] Install
  * [x] Upgrade
  * [x] Backup And Restore
  * [x] Regression

Verification links:

  * [Verification Pipeline | RHEL latest - Ansible Stable 2.8 (latest)](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1174/pipeline)
  * [Verification Pipeline | RHEL latest - Ansible Stable 2.7](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1291/pipeline)
  * [Verification Pipeline | RHEL latest - Ansible Stable 2.6](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1292/pipeline)
  * [Verification Pipeline | Ubuntu latest - Ansible Stable 2.8 (latest)](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1294/pipeline)
  * [OpenShift - Integration](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_OpenShift_Integration/505/testReport) (Failures are flakies)
