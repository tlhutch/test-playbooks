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
    * [X] ubuntu-12.04
    * [X] ubuntu-14.04
    * [X] rhel-6.5
    * [X] rhel-7.0
    * [X] centos-6.5
    * [X] centos-7.0
1. Installation completes successfully using supported ansible releases
    * [X] ansible-2.0
    * [X] ansible-1.9.x
    * [X] ansible-1.8.x (tested manually)
1. Installation completes successfully on supported images
    * [X] AMI (unlicensed)
    * [X] Vagrant

### Upgrade
1. Upgrade completes on all supported platforms from `2.1.*`
    * [X] ubuntu-12.04
    * [X] ubuntu-14.04
    * [X] rhel-6.5
    * [X] rhel-7.0
    * [X] centos-6.5
    * [X] centos-7.0
1. Upgrade completes on all supported platforms from `2.0.*`
    * [ ] ubuntu-12.04
    * [ ] ubuntu-14.04
    * [ ] rhel-6.5
    * [ ] rhel-7.0
    * [ ] centos-6.5
    * [ ] centos-7.0
1. Verify the following functions work as intended after upgrade
    * [X] Launch project_updates for existing projects
    * [X] Launch inventory_udpates for existing inventory_source
    * [X] Launch, and relaunch, existing job_templates

### Integration
1. [X] End-to-end integration completed on all supported platforms

### Feature: Job Template Status
1. [X] Verify expected tooltip
1. [X] Verify clicking a sparkline job directs the user to the expected page
1. [X] Verify sparklines are responsive to live event data

### Feature: Ad Hoc Commands
1. [X] Assert correct RBAC permission handling
1. [X] Assert ad_hoc_command detail page displays correctly
1. [X] Assert launch and relaunch with various credential types (including --become escalation) works correctly

### Feature: Backup and Restore
1. [X] Verify successful backup and restore using setup.sh
1. [X] Verify backup/restore successfully restores mongod data
1. [X] Verify backup/restore behaves as expected with remote db - (workaround needed, kbase article forethecoming)

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
1. [X] OpenStack inventory_updates complete successfully on all supported platforms
2. [X] Imported hosts include variables that allow for connectivity with ansible (e.g. ansible_ssh_host)

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
    2. [X] Verify that the files module does not appear until adding appropriate extra_vars to the scan_job
    3. [X] Verify that custom facts display correctly (created project and scan job_template and scan job)
    4. [X] Verify that actual diff-ing algorithm
    5. [X] Verify single-host compare functionality
       * [X] Verify that the left date picker accepts values older-than, or equal-to, the right date picker
       * [X] Verify that the desired scan results are selected when choosing various date-picker values
       * [X] Verify expected scan result content
    6. [X] Verify host-compare functionality
       * [X] Verify that the desired scan results are selected when choosing various date-picker values
       * [X] Verify expected scan result content - content should be correspond to correct host
    7. [X] Verify cleanup facts functionality - scheduled and manual
2. API
    1. [X] Verify desired result with various HTTP methods on system_tracking endpoints
    2. [X] Verify endpoint documentation is acceptable
    3. [X] Verify RBAC behavior with system_tracking endpoints
    4. [X] Verify bogus inputs

### Regression
1. [X] UI regression completed
1. [X] API regression completed
1. [X] Munin monitors work on all supported platforms
1. [X] Tower HA installation
    * [X] Verify successful registration of secondary instances
    * [X] Verify secondary web traffic redirects to primary (excluding /api/v1/ping/)
    * [X] Verify promoting secondary instance
    * [X] Verified tower-manage commands: [list_instances,register_instance,remove_instance,update_instance]
1. [X] Tower LDAP Integration
    * [X] Verify license enablement with legacy or enterprise license (disabled elsewhere).
    * [X] Verify Tower respects LDAP username and password on login
    * [X] Verify Tower creates user related objects on successful login (User, Teams, Organization, Admin_of_organizations).
    * [X] Verify successful login for an Organization Administrator
