# Tower 1.4.8 Release Test Plan

## Resources
* 1 full-time quality engineer (jlaska)

## Not Tested
TDB

## Features Tested

### Installation
1. Installation completes successfully on all supported platforms

### Upgrade
1. Upgrade completes on all supported platforms
2. Test upgrades using the proper username/password (should pass)
3. Test upgrades using the improper username/password (should expectedly fail)
4. Test upgrades with data, and ensure projects/inventory/jobs run post-upgrade

### Integration
1. Update automation to unified jobs API (projects/inventory_updates/jobs)
2. Add scheduler API tests
3. Add RBAC tests for scheduler

## Feature: Scheduler
1. Add scheduler API tests for inventory_sync
2. Add scheduler API tests for project_update
3. Add scheduler API tests for job_launch

## Feature: Unified Jobs View
1. Update existing job_status API automation

## Feature: Failure recovery
1. Catastrophic fail - Launch jobs, sysrq-trigger before jobs complete, all jobs should resume or failed
2. Celery fail - celery dies, we should accept jobs, but not process process.  Running jobs will be marked fail.  Resuming celery should continue running jobs.
3. Task Manager fail - task_mgr dies, should queue and start jobs, but not run.
