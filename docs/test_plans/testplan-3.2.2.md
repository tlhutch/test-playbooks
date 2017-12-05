# Tower 3.2.2 Release Test Plan

## Overview

* 3.2.2 issues available [here](https://github.com/ansible/ansible-tower/issues?utf8=%E2%9C%93&q=is%3Aopen%20is%3Aissue%20milestone%3Arelease_3.2.2)

## Resources
* 4 full-time automation engineers - cwang/jladd/mfoord/rfitzpat

## Features Not Tested

## Features Tested

* [x] Tower inventory source [Issue](https://github.com/ansible/ansible-tower/issues/6297) ([PR](https://github.com/ansible/tower/pull/551))
* [x] ovirt4.py dynamic inventory support [Issue](https://github.com/ansible/ansible-tower/issues/6522)
* [ ] Encrypted survey password defaults in the database [Issue](https://github.com/ansible/ansible-tower/issues/7046)
* [ ] Cluster-safe backup and restore [Issue](https://github.com/ansible/ansible-tower/issues/7709)

## Targeted Testing

## Regression
1. [ ] Limited manual UI testing completed
1. [ ] API regression completed
1. [ ] Tower HA regression completed
1. [x] Tower LDAP Integration regression completed
1. [x] Tower RADIUS Integration regression completed
1. [x] Social authentication regression completed
1. [x] SAML authentication
1. [ ] Verify logging (incl. cluster)
1. [ ] Backup/restore successful

### Installation
1. Installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.1/html/installandreference/requirements_refguide.html)
    * [x] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [x] rhel-7.2
    * [x] rhel-7.4 (latest)
    * [x] centos-7.latest
    * [ ] ol-7.latest
1. HA installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.1/html/administration/clustering.html#setup-considerations)
    * [ ] ubuntu-16.04
    * [x] rhel-7.2
    * [ ] rhel-7.4 (latest)
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.5 (devel branch)
    * [x] ansible-2.4
    * [x] ansible-2.3
    * [ ] ansible-2.2
1. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.1/html/installandreference/tower_installer.html#bundled-install)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. [ ] Bundled installation completes successfully for HA deployment

### Upgrades
1. [x] Upgrade completes on all supported platforms from `3.0.0` - `3.0.4`
1. [x] Upgrade completes on all supported platforms from `3.1.0` - `3.1.5`
1. [x] Upgrade completes on all supported platforms from `3.2.0` - `3.2.1`
1. [x] Verify the following functions work as intended after upgrade
    * [x] Launch project_updates for existing projects
    * [x] Launch inventory_updates for existing inventory_source
    * [x] Launch, and relaunch, existing job_templates
    * [x] Migrations were successful
    
### Post-release verification

1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
