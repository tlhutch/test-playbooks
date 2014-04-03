# Tower 1.4.8 Release Test Plan

## Resources
* 1 full-time quality engineer (jlaska)

## Not Tested
TDB

## Features Tested

### Installation
1. Installation completes successfully on all supported platforms
    [ ] ubuntu-12.04
    [ ] ubuntu-12.04 (AMI)
    [ ] ubuntu-14.04 (beta)
    [ ] rhel-6.4
    [ ] rhel-6.5
    [ ] rhel-7.0 (beta)
    [ ] centos-6.4
    [ ] centos-6.5

### Upgrade
1. Upgrade completes on all supported platforms
    [ ] ubuntu-12.04
    [ ] ubuntu-14.04 (beta)
    [ ] rhel-6.4
    [ ] rhel-6.5
    [ ] rhel-7.0 (beta)
    [ ] centos-6.4
    [ ] centos-6.5
2. Test upgrades using the proper username/password (should pass)
3. Test upgrades using the improper username/password (should use existing password, pass)
4. Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. Update automation to unified jobs API (projects/inventory_updates/jobs)
2. Add scheduler API tests
3. Add RBAC tests for scheduler

## Feature: Scheduler
1. [X] Add scheduler API tests for project_update
2. [ ] Add scheduler API tests for inventory_sync
3. [ ] Add scheduler API tests for job_launch
4. [ ] Ensure multiple jobs cant run at the same time
4. [ ] Test celeryd/task_manager recovery

## Feature: Unified Jobs View
1. Update existing job_status API automation

## Feature: Vault credential support
1. Add support for vault credential usage

## Feature: Failure recovery
1. Catastrophic fail - Launch jobs, sysrq-trigger before jobs complete, all jobs should resume or failed
2. Celery fail - celery dies, we should accept jobs, but not process process.  Running jobs will be marked fail.  Resuming celery should continue running jobs.
3. Task Manager fail - task_mgr dies, should queue and start jobs, but not run.

## Features Not Tested
1. Vault passphrase
1. Comprehensive RBAC coverage
