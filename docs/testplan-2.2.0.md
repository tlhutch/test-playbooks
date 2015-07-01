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
1. Upgrade completes on all supported platforms from `2.1.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Upgrade completes on all supported platforms from `2.0.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [ ] Existing project, inventory and job_templates relaunch successfully

### Integration
1. [ ] End-to-end integration completed on all supported platforms

### Feature: Job Template Status
1. [X] Verify expected tooltip
1. [X] Verify clicking a sparkline job directs the user to the expected page
1. [ ] Verify sparklines are responsive to live event data

### Feature: Ad Hoc Commands
1. [X] Assert correct RBAC permission handling
1. [X] Assert ad_hoc_command detail page displays correctly
1. [ ] Assert launch and relaunch with various credential types (including --become escalation) works correctly

### Feature: Product Differentiation
1. Legacy License
    * [X] Verified all existing `2.1.x` functionality remains available to users
    * [X] Verified system_tracking is not available
        * Unable to create job_templates with `type=scan`
        * Unable to launch scan jobs
        * Unable to run cleanup_facts
1. Basic License
    * [X] Verified the following features are unavailable (ldap, ha, system_tracking, multiple_organizations and activity_stream)
        * Unable to create job_templates with `type=scan`
        * Unable to launch scan jobs
        * Unable to run cleanup_facts
        * Unable to authenticate as LDAP user
        * Unable to view activity_stream data
        * Unable to create more than 1 organization
        * Unable to create and launch scan job_templates
        * Unable to promote primary or secondaries
1. Enterprise License
    * [X] Verified the following features are available
        * Able to create job_templates with `type=scan`
        * Able to launch scan jobs
        * Able to run cleanup_facts
        * Able to authenticate as LDAP user
        * Able to view activity_stream data
        * Able to create more than 1 organization
        * Able to create and launch scan job_templates
        * Able to promote primary or secondaries

### Feature: OpenStack Inventory
1. [ ] OpenStack inventory_updates complete successfully on all supported platforms
2. [ ] Imported hosts include variables that allow for connectivity with ansible (e.g. ansible_ssh_host)

### Feature: UI Refresh
1. [X] Dashboard
   * [X] Displays correctly in latest IE, Chrome and Firefox
   * [X] Responds correctly to mobile resize
   * [X] Links and tooltips work as expected
2. [X] Simplified Jobs page
3. [X] License page

### Feature: System Tracking
1. UI
    1. [X] Verify UI for single host and host-compare with no scan_jobs
    1. [X] Verify that the files module does not appear until adding appropriate extra_vars to the scan_job
    1. [X] Verify that custom facts display correctly (created project and scan job_template and scan job)
    1. [ ] Verify single-host compare functionality
       * [X] Verify that the left date picker accepts values older-than, or equal-to, the right date picker
       * [X] Verify that the desired scan results are selected when choosing various date-picker values
       * [ ] Verify expected scan result content
    1. [ ] Verify host-compare functionality
       * [X] Verify that the desired scan results are selected when choosing various date-picker values
       * [ ] Verify expected scan result content - content should be correspond to correct host
    1. [X] Verify cleanup facts functionality - scheduled and manual
1. API
    1. [ ] Verify desired result with various HTTP methods on system_tracking endpoints
    1. [ ] Verify endpoint documentation is acceptable
    1. [ ] Verify RBAC behavior with system_tracking endpoints
    1. [ ] Verify bogus inputs

### Regresion
1. [X] UI regression completed
1. [X] API regression completed
1. [X] Munin monitors work on all supported platforms
