# Tower 3.1.8 Release Test Plan

## Overview

* 3.1.8 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.1.8).

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
1. [ ] ~Backup/restore successful~
* No changes to backup-restore in this release.

### Installation
1. Standalone installation completes successfully on all supported platforms
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.2
    * [ ] rhel-7.3
    * [ ] rhel-7.4
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Standalone installation completes successfully using supported ansible releases
    * [ ] ansible-2.4
    * [ ] ansible-2.3
    * [ ] ansible-2.2
    * [ ] ansible-2.1
1. Cluster installation completes successfully using supported ansible releases
    * [ ] ansible-2.4
    * [ ] ansible-2.3
    * [ ] ansible-2.2
    * [ ] ansible-2.1
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
1. Bundled installation completes successfully on all supported platforms
    * [ ] rhel-7.2
    * [ ] rhel-7.3
    * [ ] rhel-7.4
    * [ ] centos-7.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from Tower-3.0.4.
1. [ ] Upgrade completes on all supported platforms from Tower-3.1.7.
1. [ ] Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_updates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
