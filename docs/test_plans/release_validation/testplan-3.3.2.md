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

Install:

  * [ ] Standalone
  * [ ] Standalone Bundle
  * [ ] Traditional Cluster
  * [ ] Traditional Cluster Bundle
  * [ ] OpenShift Cluster


Upgrade:

  * [ ] Standalone from latest minor
  * [ ] Standalone from latest major
  * [ ] Traditional Cluster from latest minor
  * [ ] Traditional Cluster from latest major
  * [ ] OpenShift Cluster from latest minor


Regression verifications:

  * [ ] [UI regression](https://docs.google.com/document/d/1aJGD8c2lhCC_pNp7t7s4tVrf7p0SjpajJ7R7_n8mkHA/edit#heading=h.nd7oku9karga)
  * [ ] API regression - Standalone
  * [ ] API regression - Traditional Cluster
  * [ ] API regression - OpenShift Cluster


Artifacts:

  * [ ] Build AMI (unlicensed)
  * [ ] Build Vagrant image
