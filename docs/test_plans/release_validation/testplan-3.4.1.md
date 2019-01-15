# Tower 3.4.1 Release Test Plan

## Overview

* 3.4.1 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.4.1).


## Notes

* Tower [CHANGELOG] **TBD**
* Tower-packaging [CHANGELOG] **TBD**


## Resources

* TBD


## Release prep

- Give Shane / Christian heads up about upcoming release (so they can coordinate release work with Red Hat release team)


### Verification steps

For all [supported platforms](https://docs.ansible.com/ansible-tower/3.4.0/html/installandreference/requirements_refguide.html) and [supported ansible releases](https://access.redhat.com/articles/3382771) the following processes should work:

OS supported are: RHEL7.4+ (and its derivative counter-part), Ubuntu 14.04 and 16.04
System installed Ansible versions supported are: 2.6 to stable 2.7.
Custom virtual environments may also have 2.3 to 2.5.

Install:

  * [ ] [Standalone]
  * [ ] [Standalone Bundle]
  * [ ] [Traditional Cluster with isolated nodes]
  * [ ] [Traditional Cluster Bundle with isolated nodes]
  * [ ] [OpenShift Cluster]


Upgrade:

  * [ ] [Standalone from latest minor - 3.4.1]
  * [ ] [Standalone from latest major - 3.4.1]
  * [ ] [Traditional Cluster with isolated nodes from latest minor - 3.4.1]
  * [ ] [Traditional Cluster with isolated nodes from latest major - 3.4.1]
  * [ ] [OpenShift Cluster from latest minor]


Regression verifications:

  * [ ] [UI regression]
  * [ ] [API regression - Standalone]
  * [ ] [API regression - Traditional Cluster]
  * [ ] [API regression - OpenShift Cluster]


Artifacts:

  * [ ] [AMI]
  * [ ] [Vagrant image]
  * [ ] [Documentation]
