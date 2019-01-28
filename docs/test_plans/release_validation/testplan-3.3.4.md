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

  * [x] [Standalone]
  * [x] [Traditional Cluster with isolated nodes]


Regression verifications:

  * [x] [API regression - Standalone](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Integration_Plain/260)
  * [x] [API regression - Traditional Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Integration_Cluster_Plain/57/parameters/)
  * [x] [UI Regression Testplan](https://docs.google.com/document/d/1ywu786MvepxDyNgEjNKYRpaSCCFcMFPjbbibUIPn_vo/edit#)
  * [x] [E2E against Standalone](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_E2E/1332/)
