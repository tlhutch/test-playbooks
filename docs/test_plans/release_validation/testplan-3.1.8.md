# Tower 3.1.8 Release Test Plan

## Overview

* 3.1.8 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aopen+is%3Aissue+milestone%3Arelease_3.1.8).
* Delegation of responsibilities detailed [here](https://docs.google.com/document/d/1p5ohyf0zK-WVAflE1RgQx0GGnOFLBeEJ3EJldZSlv20/edit#).
* 3.1.8 code changes shown [here](https://github.com/ansible/ansible-tower/compare/release_3.1.7...release_3.1.8)

## Notes

* Only running upgrades from latest point releases due to low risk / return.
* Other traditional regressions checks were skipped and are struckthrough with reasoning below.

## Resources
* 5 full-time automation engineers - cwang/jladd/one-t/jhill/guozhang

## Regression
1. [ ] [UI regression completed](https://docs.google.com/document/d/1fCOn33OzpuSEa4R_b8MuFJzRBITqdAZlmfM0jUcziuc/edit)
1. [ ] API regression completed - standalone
1. [ ] ~API regression completed - cluster~
* No changes to cluster-specific behavior this release.
- [x] Tower social authentication regression completed
  - [x] Google OAuth
  - [x] GitHub 
  - [x] GitHub Org
  - [x] GitHub Team
  - [x] Azure OAuth
1. [x] Tower LDAP integration regression completed
1. [x] Tower SAML integration regression completed
1. [x] Tower RADIUS integration regression completed
1. [ ] ~Logging regression completed - standalone~
1. [ ] ~Logging regression completed - cluster~
1. [ ] ~Backup/restore successful~
* No changes to backup-restore in this release.
* No changes to third-party logging this release.

### Installation
1. Standalone installation completes successfully on all supported platforms
    * [x] ubuntu-14.04
    * [x] ubuntu-16.04
    * [x] rhel-7.4
    * [x] rhel-7.5
    * [x] centos-7.latest
    * [x] ol-7.latest
1. Standalone installation completes successfully using supported ansible releases
    * [x] ansible-2.4
    * [x] ansible-2.3
    * [x] ansible-2.2
    * [x] ansible-2.1
1. Cluster installation completes successfully using supported ansible releases
    * [x] ansible-2.4
    * [x] ansible-2.3
    * [x] ansible-2.2
    * [x] ansible-2.1
1. Installation completes successfully on supported images
    * [x] AMI (unlicensed)
1. Bundled installation completes successfully on all supported platforms
    * [x] rhel-7.4
    * [x] rhel-7.5
    * [x] centos-7.latest
    * [x] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from Tower-3.0.4.
1. [x] Upgrade completes on all supported platforms from Tower-3.1.7.
1. [x] Verify the following functions work as intended after upgrade
    * [x] Launch project_updates for existing projects
    * [x] Launch inventory_updates for existing inventory_source
    * [x] Launch, and relaunch, existing job_templates
    * [x] Migrations were successful
