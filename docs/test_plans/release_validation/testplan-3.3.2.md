# Tower 3.3.2 Release Test Plan

## Overview

* 3.3.2 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.3.2).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.3.1...release_3.3.2) from 3.3.1
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.3.1...release_3.3.2) from 3.3.1


## Resources

* TBD


## Release prep

- Give Shane / Christian heads up about upcoming release (so they can coordinate release work with Red Hat release team)


### Verification steps

For all [supported platforms](https://docs.ansible.com/ansible-tower/3.3.0/html/installandreference/requirements_refguide.html) and [supported ansible releases](https://access.redhat.com/articles/3382771) the following processes should work:

OS supported are: RHEL7.4+ (and its derivative counter-part), Ubuntu 14.04 and 16.04
Ansible versions supported are: stable-2.3 to stable 2.7

Install:

  * [ ] Standalone
  * [x] [Standalone Bundle](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Bundle_Install/1730/)
  * [ ] Traditional Cluster with isolated nodes
  * [ ] Traditional Cluster Bundle
  * [x] [OpenShift Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_OpenShift_Deploy/445/)


Upgrade:

  * [ ] Standalone from latest minor
  * [ ] Standalone from latest major
  * [ ] Traditional Cluster with isolated nodes from latest minor
  * [ ] Traditional Cluster with isolated nodes from latest major
  * [x] [OpenShift Cluster from latest minor](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_OpenShift_Upgrade/22/)


Regression verifications:

  * [ ] [UI regression](https://docs.google.com/document/d/1aJGD8c2lhCC_pNp7t7s4tVrf7p0SjpajJ7R7_n8mkHA/edit#heading=h.nd7oku9karga)
  * [ ] API regression - Standalone
  * [ ] API regression - Traditional Cluster
  * [ ] API regression - OpenShift Cluster


Artifacts:

  * [x] [AMI](http://jenkins.ansible.eng.rdu2.redhat.com/job/qe-sandbox/job/Build_Tower_Image_Plain/2/)
  * [x] [Vagrant image](http://jenkins.ansible.eng.rdu2.redhat.com/job/Build_Tower_Vagrant_Box/39/)
  * [x] [Documentation](http://jenkins.ansible.eng.rdu2.redhat.com/job/Build_Tower_Docs/3007/)
