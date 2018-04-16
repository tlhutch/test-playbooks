# Tower 3.2.4 Release Test Plan

## Overview

* 3.2.4 issues available [here](https://github.com/ansible/tower/issues?q=is%3Aissue+milestone%3Arelease_3.2.4+is%3Aopen)

## Resources
* 5 full-time automation engineers - cwang/jladd/mfoord/rfitzpat/jhill

## Features Not Tested

## Features Tested

## Targeted Testing

## Regression
1. [x] Limited manual UI testing completed (jhill)
1. [x] API integration - standalone (jladd)
1. [x] API integration - HA (jladd)
1. [x] Tower/LDAP integration (rfitz)
1. [x] Tower/RADIUS integration (rfitz)
1. [x] Social authentication (jladd)
1. [x] SAML authentication (rfitz)
1. [x] Logging - standalone (cwang)
1. [x] Logging - HA (cwang)
1. [x] Backup/restore - standalone (jladd)
1. [x] Backup/restore - HA (jladd)

### Installation
1. Installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/requirements_refguide.html) (jladd)
    * [x] ubuntu-14.04
    * [x] ubuntu-16.04
    * [x] rhel-7.2
    * [x] rhel-7.4 (latest)
    * [x] centos-7.latest
    * [x] ol-7.latest
1. Installation completes successfully using supported ansible releases (jladd)
    * [x] ansible-2.6 (devel)
    * [x] ansible-2.5
    * [x] ansible-2.4
    * [x] ansible-2.3
    * [x] ansible-2.2
1. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/tower_installer.html#bundled-install) (jladd)
    * [x] rhel-7.latest
    * [x] centos-7.latest
    * [x] ol-7.latest
1. [x] Installation completes successfully for HA deployment (RHEL-7.2) (jladd)
1. [x] Bundled installation completes successfully for HA deployment (jladd)

### Upgrades
1. [x] Successful migrations from `3.0.0` - `3.0.4` (jhill)
1. [x] Successful migrations from `3.1.0` - `3.1.5` (jhill)
1. [x] Successful upgrades on all supported platforms from `3.0.4` - standalone (rfitz / jhill)
1. [x] Successful upgrades on all supported platforms from `3.1.5` - standalone (rfitz)
1. [x] Successful upgrades on all supported platforms from `3.2.0` - `3.2.3` - standalone (rfitz)
1. [x] Successful upgrades on all supported platforms from `3.2.0` - `3.2.3` - HA (cwang)

* Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [x] AMI (unlicensed) (jladd)
    * [x] Vagrant (jladd)
