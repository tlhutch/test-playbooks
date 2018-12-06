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

  * [x] [Standalone](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Install/1167/)
  * [x] [Standalone Bundle](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Bundle_Install/1730/)
  * [x] [Traditional Cluster with isolated nodes](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_Install_Cluster/1518/)
  * [x] [Traditional Cluster Bundle with isolated nodes](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/qe-sandbox/job/Test_Tower_Install_Cluster_Plain/167/)
  * [x] [OpenShift Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_OpenShift_Deploy/445/)


Upgrade:

  * [x] [Standalone from latest minor - 3.3.1](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Upgrade/3434/) + #3435 (Ubuntu 14.04 passed when ran manually)
  * [x] [Standalone from latest major - 3.2.8](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_Upgrade/3437/) + #3438
  * [x] [Traditional Cluster with isolated nodes from latest minor - 3.3.1](http://jenkins.ansible.eng.rdu2.redhat.com/job/qe-sandbox/job/Test_Tower_Upgrade_Plain/545/)
  * [x] [Traditional Cluster with isolated nodes from latest major - 3.2.8](http://jenkins.ansible.eng.rdu2.redhat.com/job/qe-sandbox/job/Test_Tower_Upgrade_Plain/546/)
  * [x] [OpenShift Cluster from latest minor](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_OpenShift_Upgrade/22/)


Regression verifications:

  * [ ] [UI regression](https://docs.google.com/document/d/1aJGD8c2lhCC_pNp7t7s4tVrf7p0SjpajJ7R7_n8mkHA/edit#heading=h.nd7oku9karga)
  * [x] [API regression - Standalone](http://jenkins.ansible.eng.rdu2.redhat.com/job/qe-sandbox/job/Test_Tower_Integration_Plain/133/testReport/)
  * [x] [API regression - Traditional Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/qe-sandbox/job/Test_Tower_Integration_Cluster_Plain/31/) 8 failures - fixed/flaky
  * [x] [API regression - OpenShift Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_OpenShift_Integration/357/) - 11 failures tested manually / flaky


Artifacts:

  * [x] [AMI](http://jenkins.ansible.eng.rdu2.redhat.com/job/qe-sandbox/job/Build_Tower_Image_Plain/2/)
  * [x] [Vagrant image](http://jenkins.ansible.eng.rdu2.redhat.com/job/Build_Tower_Vagrant_Box/39/)
  * [x] [Documentation](http://jenkins.ansible.eng.rdu2.redhat.com/job/Build_Tower_Docs/3007/)
