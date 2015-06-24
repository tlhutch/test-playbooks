# Tower 2.2.0 Release Test Plan

## Resources
* 1 full-time quality engineer - cwang
* 1 part-time quality engineer - jlaska

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested
1. Comprehensive RBAC coverage is covered in API unit and integration tests, but not explicitly in the UI testing.

## Features Tested

### Installation
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
    * [ ] ansible-1.8.x
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant

### Upgrade
1. Upgrade completes on all supported platforms from 2.1.*
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Upgrade completes on all supported platforms from 2.0.*
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. [ ] Test upgrades using correct and incorrect values for the following fields: [admin_password, pg_password, redis_password, munin_password]
1. [ ] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [ ] End-to-end integration completed on all supported platforms

### Feature: Job Template Status
1. [X] Verify expected tooltip
1. [X] Verify clicking a sparkline job directs the user to the expected page
1. [] Verify sparklines are responsive to live event data

### Feature: Ad Hoc Commands
1. [X] Assert correct RBAC permission handling
1. [X] Assert ad_hoc_command detail page displays correctly
1. [ ] Assert launch and relaunch with various credential types (including --become escalation) works correctly

### Feature: Product Differentiation
1. [ ] Legacy License
1. [ ] Basic License
1. [ ] Enterprise License

### Feature: OpenStack Inventory
1. [ ] OpenStack inventory_updates complete successfully on all supported platforms
1. [ ] Imported hosts include variables that allow for connectivity with ansible (e.g. ansible_ssh_host)

### Feature: UI Refresh
1. Dashboard
   * [ ] Displays correctly in latest IE, Chrome and Firefox
   * [ ] Responds correctly to mobile resize
   * [ ] Links and tooltips work as expected
1. [ ] Simplified Jobs page
1. [ ] License page

### Feature: System Tracking
1. [ ] Check no-scan screen for both single host and host compare

### Regresion
1. [ ] UI regression completed
1. [ ] API regression completed
1. [ ] Munin monitors work on all supported platforms
