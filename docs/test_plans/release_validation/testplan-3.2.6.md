# Tower 3.2.6 Release Test Plan

## Overview

* 3.2.6 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.2.6). 

## Notes

* Only running upgrades from latest point releases due to low risk / return.
* Other traditional regressions checks were skipped and are struckthrough with reasoning below.

## Resources
* 5 full-time automation engineers - cwang/jladd/one-t/jhill/guozhang

## Regression
1. [ ] [UI regression completed](https://docs.google.com/document/d/1fCOn33OzpuSEa4R_b8MuFJzRBITqdAZlmfM0jUcziuc/edit)
1. [ ] API regression completed - standalone
1. [ ] API regression completed - cluster
1. [ ] Tower social authentication regression completed
1. [ ] Tower LDAP integration regression completed
1. [ ] Tower SAML integration regression completed
1. [ ] Tower RADIUS integration regression completed
1. [ ] ~Logging regression completed - standalone~
1. [ ] ~Logging regression completed - cluster~
1. [ ] ~Backup/restore successful - standalone~
1. [ ] ~Backup/restore successful - cluster~
* No changes to backup-restore in this release.
* No changes to third-party logging this release.

### Installation
1. Standalone installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/requirements_refguide.html)
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.2
    * [ ] rhel-7.4 (latest)
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Standalone installation completes successfully using supported ansible releases
    * [ ] ansible-2.6
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3
    * [ ] ansible-2.2
1. Cluster installation completes successfully using supported ansible releases
    * [ ] ansible-2.6
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3
    * [ ] ansible-2.2
1. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/tower_installer.html#bundled-install)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. [ ] Bundled installation completes successfully for HA deployment

### Upgrades
1. [ ] Upgrade completes on all supported platforms from Tower-3.1.7 - standalone
1. [ ] Upgrade completes on all supported platforms from Tower-3.2.5 - standalone
1. [ ] Upgrade completes on all supported platforms from Tower-3.2.5 - cluster
* Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
