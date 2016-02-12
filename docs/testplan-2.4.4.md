# Tower 2.4.4 Release Test Plan

## Resources
* 3 full-time quality engineers - cwang, jladdjr, jakemcdermott

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested

## Features Tested

### Regression
1. [ ] UI regression completed (Jake)
1. [ ] API regression completed (Automated)
1. [ ] Munin monitors work on all supported platforms (Chris)
1. [ ] Tower HA installation (Jim)
    * [ ] Verify successful registration of secondary instances
    * [ ] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [ ] Verify promoting secondary instance
    * [ ] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [x] Tower LDAP Integration (Chris)
    * [x] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [x] Verify Tower respects LDAP username and password on login
    * [x] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [x] Verify successful login for an Organization Administrator

#### Installation online installer
1. Installation completes successfully on all supported platforms (Chris)
    * [x] ubuntu-12.04
    * [x] ubuntu-14.04
    * [x] rhel-6.7
    * [x] rhel-7.2
    * [x] centos-6.7
    * [x] centos-7.1
1. Installation completes successfully using supported ansible releases (Chris)
    * [x] ansible-2.0
    * [x] ansible-1.9.x
    * [x] ansible-1.8.x (manually tested on EL platforms)
1. Installation completes successfully on supported images (Jim)
    * [ ] AMI (unlicensed)
    * [ ] Vagrant

#### Installation bundle installer
1. Installation completes successfully on all supported platforms (* Test on Ansible 1.9?)
    * [ ] rhel-6.7
    * [ ] rhel-7.2
    * [ ] centos-6.7
    * [ ] centos-7.1

#### Upgrade installer
1. Upgrade completes on all supported platforms from `2.3.*` (Chris)
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.7
    * [ ] rhel-7.2
    * [ ] centos-6.7
    * [ ] centos-7.2
1. Upgrade completes on all supported platforms from `2.2.*` (Jim)
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.7
    * [ ] rhel-7.2
    * [ ] centos-6.7
    * [ ] centos-7.2
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
