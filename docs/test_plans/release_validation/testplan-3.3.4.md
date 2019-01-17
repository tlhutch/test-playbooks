# Tower 3.3.4 Release Test Plan

## Overview

* 3.3.4 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.3.4).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.3.3...release_3.3.4)
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.3.3...release_3.3.4)


## Resources

* Elijah DeLee + Yanis Guenane


### Verification steps

For all [supported platforms](https://docs.ansible.com/ansible-tower/3.3.0/html/installandreference/requirements_refguide.html) and [supported ansible releases](https://access.redhat.com/articles/3382771) the following processes should work:

OS supported are: RHEL7.4+ (and its derivative counter-part), Ubuntu 14.04 and 16.04
Ansible versions supported are: stable-2.3 to stable 2.7

Install:

  * [ ] [Standalone]
  * [ ] [Standalone Bundle]
  * [ ] [Traditional Cluster with isolated nodes]
  * [ ] [Traditional Cluster Bundle with isolated nodes]
  * [ ] [OpenShift Cluster]


Upgrade:

  * [ ] [Standalone from latest minor - 3.3.4]
  * [ ] [Standalone from latest major - 3.3.4]
  * [ ] [Traditional Cluster with isolated nodes from latest minor - 3.3.4]
  * [ ] [Traditional Cluster with isolated nodes from latest major - 3.3.4]
  * [ ] [OpenShift Cluster from latest minor]


Regression verifications:

  * [ ] [API regression - Standalone]
  * [ ] [API regression - Traditional Cluster]
  * [ ] [API regression - OpenShift Cluster]
  * [ ] [UI Regression Testplan](https://docs.google.com/document/d/1ywu786MvepxDyNgEjNKYRpaSCCFcMFPjbbibUIPn_vo/edit#)


Artifacts:

  * [ ] [AMI]
  * [ ] [Vagrant image]
  * [ ] [Documentation]
