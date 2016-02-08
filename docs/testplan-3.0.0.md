# Tower 3.0.0 Release Test Plan

## Resources
* 3 full-time quality engineers - cwang/jladd/jmcdermott

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested

## Features Tested

### Database Config (e.g. /api/v1/settings)
1. []  
 
### Regression
1. [] UI regression completed
1. [] API regression completed
1. [] Munin monitors work on all supported platforms
1. [] Tower HA installation
    * [] Verify successful registration of secondary instances
    * [] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [] Verify promoting secondary instance
    * [] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [] Tower LDAP Integration
    * [] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [] Verify Tower respects LDAP username and password on login
    * [] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [] Verify successful login for an Organization Administrator

#### Installation online installer
1. Installation completes successfully on all supported platforms
    * [] ubuntu-12.04
    * [] ubuntu-14.04
    * [] rhel-6.7
    * [] rhel-7.2
    * [] centos-6.7
    * [] centos-7.1
1. Installation completes successfully using supported ansible releases
    * [] ansible-2.0
    * [] ansible-1.9.x
    * [] ansible-1.8.x (manually tested on EL platforms)
1. Installation completes successfully on supported images
    * [] AMI (unlicensed)
    * [] Vagrant

#### Installation bundle installer
1. Installation completes successfully on all supported platforms
    * [] rhel-6.7
    * [] rhel-7.2
    * [] centos-6.7
    * [] centos-7.1

#### Upgrade installer
1. Upgrade completes on all supported platforms from `2.4.*`
    * [] ubuntu-12.04
    * [] ubuntu-14.04
    * [] rhel-6.7
    * [] rhel-7.2
    * [] centos-6.7
    * [] centos-7.1
1. Upgrade completes on all supported platforms from `2.3.*`
    * [] ubuntu-12.04
    * [] ubuntu-14.04
    * [] rhel-6.7
    * [] rhel-7.2
    * [] centos-6.7
    * [] centos-7.1
1. Verify the following functions work as intended after upgrade
    * [] Launch project_updates for existing projects
    * [] Launch inventory_udpates for existing inventory_source
    * [] Launch, and relaunch, existing job_templates
