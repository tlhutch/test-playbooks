# Tower 2.4.0 Release Test Plan

## Resources
* 1 full-time quality engineer - cwang
* 1 part-time quality engineer - jlaska

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested
1. Comprehensive RBAC coverage is covered in API unit and integration tests, but not explicitly in the UI testing.

## Features Tested

### Installation online installer
1. Installation completes successfully on all supported platforms
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.0
    * [ ] ansible-1.9.x
    * [ ] ansible-1.8.x (not tested on *all* platforms)
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed) [jlaska]
    * [ ] Vagrant [jlaska]

### Installation bundle installer
1. Installation completes successfully on all supported platforms
    * [ ] rhel 6.5
    * [ ] rhel 6.6
    * [ ] rhel 6.7
    * [ ] rhel 7.0
    * [ ] rhel 7.1
    * [ ] centos 6.5
    * [ ] centos 6.6
    * [ ] centos 6.7
    * [ ] centos 7.0
    * [ ] centos 7.1

### Upgrade online installer
1. Upgrade completes on all supported platforms from `2.2.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Upgrade completes on all supported platforms from `2.1.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_udpates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates

### Integration
1. [ ] End-to-end integration completed on all supported platforms

### Regression
1. [ ] Comprehensive RBAC coverage using EuroNext and NeuStar datasets
1. [ ] UI regression completed
1. [ ] API regression completed
1. [ ] Munin monitors work on all supported platforms
1. [ ] Tower HA installation [jlaska]
    * [ ] Verify successful registration of secondary instances
    * [ ] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [ ] Verify promoting secondary instance
    * [ ] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [ ] Tower LDAP Integration [jlaska]
    * [ ] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [ ] Verify Tower respects LDAP username and password on login
    * [ ] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [ ] Verify successful login for an Organization Administrator
