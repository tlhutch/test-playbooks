# Tower 2.3.0 Release Test Plan

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
    * [] ubuntu-12.04
    * [] ubuntu-14.04
    * [] rhel-6.5
    * [] rhel-7.0
    * [] centos-6.5
    * [] centos-7.0
1. Installation completes successfully using supported ansible releases
    * [] ansible-2.0
    * [] ansible-1.9.x
    * [] ansible-1.8.x (tested manually)
1. Installation completes successfully on supported images
    * [] AMI (unlicensed)
    * [] Vagrant

### Installation offline installer
1. Installation completes successfully on all supported platforms
    * [] rhel 6.5
    * [] rhel 6.6
    * [] rhel 6.7
    * [] rhel 7.0
    * [] rhel 7.1 
    * [] centos 6.5
    * [] centos 6.6
    * [] centos 6.7
    * [] centos 7.0
    * [] centos 7.1

### Upgrade online installer
1. Upgrade completes on all supported platforms from `2.1.*`
    * [] ubuntu-12.04
    * [] ubuntu-14.04
    * [] rhel-6.5
    * [] rhel-7.0
    * [] centos-6.5
    * [] centos-7.0
1. Upgrade completes on all supported platforms from `2.0.*`
    * [] ubuntu-12.04
    * [] ubuntu-14.04
    * [] rhel-6.5
    * [] rhel-7.0
    * [] centos-6.5
    * [] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [] Launch project_updates for existing projects
    * [] Launch inventory_udpates for existing inventory_source
    * [] Launch, and relaunch, existing job_templates

### Upgrade offline installer
1. Upgrade completes on all supported platforms from `2.1.*`
    * [] rhel-6.5
    * [] rhel-7.0
    * [] centos-6.5
    * [] centos-7.0
1. Upgrade completes on all supported platforms from `2.0.*`
    * [] rhel-6.5
    * [] rhel-7.0
    * [] centos-6.5
    * [] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [] Launch project_updates for existing projects
    * [] Launch inventory_udpates for existing inventory_source
    * [] Launch, and relaunch, existing job_templates

### Integration
1. [] End-to-end integration completed on all supported platforms

### Feature: Offline installer 
1. [] Running the installer on the same box as Tower
1. [] Running the installer on a different box as Tower and connecting remotely (sudo and su)
1. [] Installer is single downloadable object
1. [] Installer signed by Ansible 
1. [] Installer contains all non-vendor dependencies, Ansible, and Tower
1. [] Installation of non-vendor dependencies should not require internet access
1. [] Installer includes list of vendor repositories
1. [] Installer should leave pre-existing versions of Ansible intact 
1. [] Integration passes 

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
