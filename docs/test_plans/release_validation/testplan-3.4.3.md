# Tower 3.4.3 Release Test Plan

## Overview

* 3.4.3 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.4.3).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.4.2...release_3.4.3)
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.4.2...release_3.4.3)


### Verification steps

This is a CVE-related maintenance release. Only the OpenShift installer is impacted.
Numbers of steps to verify this release will be narrowed to only necessary tests.

Install:

  * [x] [OpenShift Cluster](http://jenkins.ansible.eng.rdu2.redhat.com/view/Tower/job/Test_Tower_OpenShift_Deploy/565/)


Upgrade:

  * [x] [OpenShift Cluster from latest minor (3.4.2)](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_OpenShift_Upgrade/36)
  * [x] [OpenShift Cluster from latest major (3.3.4)](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_OpenShift_Upgrade/37)


Regression verifications:

  * [x] [API regression - OpenShift](http://jenkins.ansible.eng.rdu2.redhat.com/job/Test_Tower_OpenShift_Integration/447/)
