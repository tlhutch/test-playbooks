# Tower 3.3.1 Release Test Plan

## Overview

* 3.3.1 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.3.1).

## Notes

* First release to support OpenShift upgrade
* Starting from this release, result from the final sign off run should be archived and linked here
* Tower [CHANGELOG](https://github.com/ansible/tower/compare/release_3.3.0...release_3.3.1) from 3.3.0
* Tower-packaging [CHANGELOG](https://github.com/ansible/tower-packaging/compare/release_3.3.0...release_3.3.1) from 3.3.0

## Resources

* TBD

## Regression

1. [ ] UI regression completed
2. [ ] API regression completed - standalone
3. [ ] API regression completed - traditional cluster
4. [ ] API regression completed - OpenShift

### Installation

1. Standalone installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.3.0/html/installandreference/requirements_refguide.html)
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.4
    * [ ] rhel-7.5
    * [ ] centos-7.latest
    * [ ] ol-7.latest

2. Cluster installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.3.0/html/installandreference/requirements_refguide.html)
    * [ ] ubuntu-16.04
    * [ ] rhel-7.5

3. Standalone installation completes successfully using [supported ansible releases](https://access.redhat.com/articles/3382771)
    * [ ] ansible-2.7
    * [ ] ansible-2.6
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3

4. Cluster installation completes successfully using [supported ansible releases](https://access.redhat.com/articles/3382771)
    * [ ] ansible-2.7
    * [ ] ansible-2.6
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3

5. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.3.0/html/installandreference/tower_installer.html#bundled-install)
    * [ ] rhel-7.4
    * [ ] rhel-7.5
    * [ ] centos-7.latest
    * [ ] ol-7.latest

6. [ ] Bundled installation completes successfully for clustered deployment

### Upgrades

1. [ ] Upgrade completes on all supported platforms from Tower-3.2.7 - standalone
2. [ ] Upgrade completes on all supported platforms from Tower-3.3.0 - standalone
3. [ ] Upgrade completes from RHEL 7.5 from Tower-3.3.0 - cluster
3. [ ] Upgrade completes from Tower-3.3.0 - OpenShift

Verify the following functionality after upgrade:

  * Resource migrations
  * Launch project_updates for existing projects
  * Launch inventory_updates for existing inventory_source
  * Launch, and relaunch, existing job_templates

### Provided Images

1. Installation completes successfully on supported images;

    * [ ] AMI (unlicensed)
    * [ ] Vagrant

### Misc

1. [ ] Archive result from the sign-off run and attach them in here.
