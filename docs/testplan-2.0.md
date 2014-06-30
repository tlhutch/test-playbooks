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

2. Verify AWS AMI boot successfully, and include the appropriate license information
    [ ] license: 10
    [ ] license: 50
    [ ] license: 100
    [ ] license: 250

### Upgrade
1. Upgrade completes on all supported platforms
    [ ] ubuntu-12.04
    [ ] ubuntu-14.04
    [ ] rhel-6.5
    [ ] rhel-7.0 (beta)
    [ ] centos-6.5
2. [ ] Test upgrades using correct and incorrect values for the following fields: [admin_password, pg_password, rabbitmq_password]
3. [ ] Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. [ ] End-to-end integration completed on all supported platforms

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
