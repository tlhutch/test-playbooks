# Tower 3.4.1 Release Test Plan

## Overview

* 3.4.1 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.4.1).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.4.0...release_3.4.1)
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.4.0...release_3.4.1)


## Resources

* Elijah DeLee + Yanis Guenane


### Verification steps

OS supported are: RHEL7.4+ (and its derivative counter-part)
System installed Ansible versions supported are: 2.6 to stable 2.7.
Custom virtual environments may also have 2.3 to 2.5.

* No changes were deemed to have an impact that would differ accross platforms, so we cut down the platforms tested.
* No changes were deemed to have large upgrade impact so number of prior versions to test upgrade from was cut down.

Install:

  * [x] [Standalone](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Install/1301)
  * [ ] [Standalone Bundle]
  * [x] [Traditional Cluster with isolated nodes](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Install/1302/parameters/)
  * [ ] [Traditional Cluster Bundle with isolated nodes]
  * [ ] [OpenShift Cluster]


Upgrade:

  * [x] Standalone from latest minor - 3.4.1 as part of manually testing insights URL upgrade
  * [x] Standalone from latest major - 3.4.1 as part of manually testing social auth upgrade

Regression verifications:

  * [x] [API regression - Standalone](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration/ANSIBLE_NIGHTLY_BRANCH=stable-2.7,PLATFORM=rhel-7.6-x86_64,label=jenkins-jnlp-agent/5277/parameters/)_
  * [x] [API regression - Traditional Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration_Cluster/ANSIBLE_NIGHTLY_BRANCH=stable-2.7,PLATFORM=rhel-7.6-x86_64,label=jenkins-jnlp-agent/1161/)
  * [ ] [API regression - OpenShift Cluster]

 Additional Manual Verification:

  * [x] Configure users with github auth with 3.3.2, upgrade to 3.4.1, verify all users can authenticate

Artifacts:

  * [ ] [AMI]
  * [ ] [Vagrant image]
  * [ ] [Documentation]
