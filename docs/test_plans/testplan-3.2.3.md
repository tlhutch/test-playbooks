# Tower 3.2.3 Release Test Plan

## Overview

* 3.2.3 issues available [here](https://github.com/ansible/ansible-tower/issues?utf8=%E2%9C%93&q=is%3Aopen%20is%3Aissue%20milestone%3Arelease_3.2.3)

## Resources
* 4 full-time automation engineers - cwang/jladd/mfoord/rfitzpat

## Features Not Tested

## Features Tested

## Targeted Testing

## Regression
1. [x] Limited manual UI testing completed
1. [x] API integration - standalone
1. [ ] API integration - HA
1. [x] Tower/LDAP integration
1. [ ] Tower/RADIUS integration
1. [ ] Social authentication
1. [ ] SAML authentication
1. [ ] Logging - standalone
1. [ ] Logging - HA
1. [x] Backup/restore - standalone
1. [ ] Backup/restore - HA

### Installation
1. Installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.2/html/installandreference/requirements_refguide.html)
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.2
    * [ ] rhel-7.4 (latest)
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.5 (devel branch)
    * [ ] ansible-2.4
    * [ ] ansible-2.3
    * [ ] ansible-2.2
1. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.2/html/installandreference/tower_installer.html#bundled-install)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. [ ] Installation completes successfully for HA deployment (RHEL-7.2)
1. [ ] Bundled installation completes successfully for HA deployment

### Upgrades
1. [x] Successful migrations from `3.0.0` - `3.0.4`
1. [x] Successful migrations from `3.1.0` - `3.1.5`
1. [ ] Successful upgrades on all supported platforms from `3.0.4` - standalone
1. [x] Successful upgrades on all supported platforms from `3.1.5` - standalone
1. [ ] Successful upgrades on all supported platforms from `3.2.0` - `3.2.2` - standalone
1. [x Successful upgrades on all supported platforms from `3.2.0` - `3.2.2` - HA
1. Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [x] AMI (unlicensed)
    * [x] Vagrant
