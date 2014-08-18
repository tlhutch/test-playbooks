# Tower 2.0.0 Release Test Plan

## Resources
* 1 full-time quality engineer (jlaska)
* 1 full-time quality engineer (wrosario -- ETA 2014-Jun-30)

## Assumptions
1. UI testing is performed manually.  While basic automated coverage exists, it is insufficient to test customer workflows.

## Features Not Tested
1. Comprehensive RBAC coverage

## Features Tested

### Installation
1. Installation completes successfully on all supported platforms
    [ ] ubuntu-12.04
    [ ] ubuntu-14.04
    [ ] rhel-6.5
    [ ] rhel-7.0
    [ ] centos-6.5

2. Verify AWS AMI boot successfully, and includes the expected license information
    [ ] license: 10
    [ ] license: 50
    [ ] license: 100
    [ ] license: 250

### Upgrade
1. Upgrade completes on all supported platforms
    [ ] ubuntu-12.04
    [ ] ubuntu-14.04
    [ ] rhel-6.5
    [ ] rhel-7.0
    [x] centos-6.5 (manual)
2. [X] Test upgrades using correct and incorrect values for the following fields: [admin_password, pg_password, rabbitmq_password]
3. [ ] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [ ] End-to-end integration completed on all supported platforms

### Feature: trial license
1. [ ] Automated API tests
       > no license - can't launch jobs and can't add hosts
       > expired trial license - can't launch jobs and can't add hosts
       > expired license, within grace_period - can launch jobs and can add hosts
       > expired license, within grace_period but hosts exceeded - can't launch jobs or can add hosts
       > expired license, beyond grace_period - can't launch jobs or add hosts
       > able to POST a new license
       > able to POST a new license (going from AWS -> Normal)
       > Verified that a Trial license has _no_ grace period
2. [ ] UI tests
       > no license - verify login dialog, and POST license
       > expired trial license - verify login prompt and wording in about->license
       > expired license, within grace_period - verify login prompt and wording in about->license
       > expired license, beyond grace_period - verify login prompt and wording in about->license

### Feature: ansible-tower service
1. [ ] Verify ansible-tower start/stop/restart/status on all platforms
       [ ] ubuntu-12.04
       [ ] ubuntu-14.04
       [ ] rhel-6.5
       [ ] rhel-7.0
       [ ] centos-6.5
1. [X] Verify ansible-tower is used by setup playbook

### Feature: socket-io asynchronous updates
1. [ ] Verify asynchronous project_update (success, cancelled, failure, error)
1. [ ] Verify asynchronous inventory_source (success, cancelled, failure, error)
1. [ ] Verify asynchronous job (success, cancelled, failure, error)

### Feature: socket-io job_events
1. [ ] Verify expected job events are available from /jobs/N/events
1. [ ] Verify socket.io sends the right events
1. [ ] UI performance with the following playbooks:
       * 2500 tasks, 200 hosts
       * 200 tasks, 2500 hosts
       * identify where things start to breakdown
1. [ ] Verify client memory requirements, does it scale
1. [ ] Verify that the events sent via socket-io, match the events sent via endpoint /jobs/N/job_events?
1. [ ] Verify job page in supported browsers
       * ff latest
       * chrome latest
       * safari latest

### UI Regresion
1. [ ] Verify links from Dashboard are correct
2. [ ] Verify organization CRUD
3. [ ] Verify user CRUD
4. [ ] Verify team CRUD
5. [ ] Verify project CRUD
6. [ ] Verify inventory CRUD
7. [ ] Verify group CRUD
8. [ ] Verify host CRUD
9. [ ] Verify job_template CRUD
10. [ ] Verify job CRUD
11. [ ] Verify job dialog tabs for various job types present correct information
12. [ ] Verify tower menu displays and works on a smaller resolution
