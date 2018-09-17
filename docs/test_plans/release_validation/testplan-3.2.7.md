# Tower 3.2.7 Release Test Plan

## Overview

* 3.2.7 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.2.7).
* Delegation of responsibilities detailed [here](https://docs.google.com/document/d/1NguDSRSj9gx3-aiC4_5cKoHvfWeJrmgw2i0iEVp8HQM/edit#).

## Notes

* Only one issue made its way into Tower-3.2.7, which details a way to exploit the API to gain secrets. Because we only have a
single API-side change, only upgrades and install tests and integration are needed to vet this release.
* Only API-side change is [here](https://github.com/ansible/tower/pull/2902/files), which is minimal.
* Only running upgrades from latest point releases due to low risk / return.

## Resources
* 4 full-time automation engineers - cwang/jladd/one-t/jhill

## Regression
1. [ ] ~UI regression completed~
1. [ ] API regression completed - standalone
1. [ ] API regression completed - cluster
- [ ] ~Tower social authentication regression completed~
  - [ ] ~Google OAuth~
  - [ ] ~GitHub~
  - [ ] ~GitHub Org~
  - [ ] ~GitHub Team~
  - [ ] ~Azure OAuth~
1. [ ] ~Tower LDAP integration regression completed~
1. [ ] ~Tower SAML integration regression completed~
1. [ ] ~Tower RADIUS integration regression completed~
1. [ ] ~Logging regression completed - standalone~
1. [ ] ~Logging regression completed - cluster~
1. [ ] ~Backup/restore successful - standalone~
1. [ ] ~Backup/restore successful - cluster~

### Installation
1. Standalone installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.6/html/installandreference/requirements_refguide.html)
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.4
    * [ ] rhel-7.5
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Standalone installation completes successfully using supported ansible releases
    * [ ] ansible-2.6
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3
1. Cluster installation completes successfully using supported ansible releases
    * [ ] ansible-2.6
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3
1. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/tower_installer.html#bundled-install)
    * [ ] rhel-7.4
    * [ ] rhel-7.5
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. [ ] ~Bundled installation completes successfully for clustered deployment~

### Upgrades
1. [x] Upgrade completes on all supported platforms from Tower-3.1.8 - standalone
1. [x] Upgrade completes on all supported platforms from Tower-3.2.6 - standalone
1. [x] Upgrade completes on all supported platforms from Tower-3.2.6 - cluster
* Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
