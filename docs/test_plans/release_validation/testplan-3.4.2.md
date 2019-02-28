# Tower 3.4.2 Release Test Plan

## Overview

* 3.4.2 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.4.2).


## Notes

* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.4.1...release_3.4.2)
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.4.1...release_3.4.2)


### Verification steps

OS supported are: RHEL7.4+ (and its derivative counter-part)
System installed Ansible versions supported are: 2.6 to stable 2.7.
Custom virtual environments may also have 2.3 to 2.5.


Install:

  * [ ] Standalone
  * [ ] Standalone Bundle
  * [ ] Traditional Cluster with isolated nodes
  * [ ] Traditional Cluster with isolated nodes bundle
  * [ ] OpenShift Cluster


Upgrade:

  * [ ] Standalone from latest minor (3.4.1)
  * [ ] Standalone from latest major (3.3.4)
  * [ ] Standalone Bundle from latest minor (3.4.1)
  * [ ] Standalone Bundle from latest major (3.3.4)
  * [ ] Traditional Cluster with isolated nodes from latest minor (3.4.1)
  * [ ] Traditional Cluster with isolated nodes from latest major (3.3.4)
  * [ ] Traditional Cluster with isolated nodes bundle from latest minor (3.4.1)
  * [ ] Traditional Cluster with isolated nodes bundle from latest major (3.3.4)
  * [ ] OpenShift Cluster from latest minor (3.4.1)
  * [ ] OpenShift Cluster from latest major (3.3.4)


Regression verifications:

  * [ ] API regression - Standalone
  * [ ] API regression - Traditional Cluster with isolated nodes
  * [ ] E2E against Standalone
  * [ ] E2E against Cluster
  * [x] [UI Manual Regression Testing](https://docs.google.com/document/d/1c1m63MB52T3McNhWNoyjTizcsPVtgCgEf1hlL9G_Hlo/edit#heading=h.nkkhxexfvgsb)
