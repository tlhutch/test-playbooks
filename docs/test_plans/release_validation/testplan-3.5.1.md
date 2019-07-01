# Tower 3.5.1 Release Test Plan

## Overview

* 3.5.1 issues available [here](https://github.com/orgs/ansible/projects/9).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.5.0...release_3.5.1)
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.5.0...release_3.5.1)


### Verification steps

On RHEL7 latest, RHEL8 latest and Ubuntu latest:

  * [x] Install
  * [x] Upgrade
  * [x] Backup And Restore
  * [x] Regression


Verification links:

  * [Verification Pipeline | RHEL 8 latest - Ansible Stable 2.8 (latest)](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1339/pipeline)
  * [Verification Pipeline | RHEL 7 latest - Ansible Stable 2.8 (latest)](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1228/pipeline)
  * [Verification Pipeline | RHEL 7 latest - Ansible Stable 2.7](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1229/pipeline)
  * [Verification Pipeline | RHEL 7 latest - Ansible Stable 2.6](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1230/pipeline)
  * [Verification Pipeline | Ubuntu latest - Ansible Stable 2.8 (latest)](http://jenkins.ansible.eng.rdu2.redhat.com/blue/organizations/jenkins/Pipelines%2Fverification-pipeline/detail/verification-pipeline/1335/pipeline)
  * [OpenShift - Integration](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_OpenShift_Integration/502/testReport/) (Failures are flakies)
