# Tower 3.4.0 Release Test Plan

## Resources
* 6 full-time engineers (yanis, mat, john, jim, elijah, danny)
* Initial planning document for whole engineering org (api + ui + qe) [here](https://docs.google.com/spreadsheets/d/1Dc287lghj1CYR24s853671l-P5RXtpwZNcir0olt5Zc/edit#gid=161330338)

## Features Tested

### Auto-splitting of jobs (mat + john)
* [Feature]()
* [API Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_job_slicing.md)
* [UI Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_job_slicing_ui.md)
- [x] Testing complete

### Workflow Convergence Node (jim + elijah + danny)
* [Feature]()
* [API Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_workflow_convergence.md)
* [UI Test Plan](https://docs.google.com/document/d/1U9VgxNoTw6CPpWbqKPomglmAK50xW3IaCif_BKZNc2o)
- [ ] Testing complete

### Workflow-Level Inventory (elijah + john)
* [Feature]()
* [API + UI Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_workflow_level_inventory.md)
- [ ] Testing complete

### Workflows within Workflows (yanis + john)
* [Feature]()
* [API + UI Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_workflow_in_workflow.md)
- [ ] Testing complete

### Workflows Always Nodes Allowed in Conjunction With Other Nodes (elijah + danny)
* [Feature]()
* [API + UI Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_always_nodes_allowed_with_other_nodes.md)
- [x] Testing complete

### Source all Content from releases.ansible.com (elijah) (packaging only)
* [Feature]()
* [Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/packaging/34-ensure-no-third-party-packages.md)
- [ ] Testing complete


### Finish Organization Permission Views (danny) (ui only)
* [Feature]()
* [UI Test Plan](https://docs.google.com/document/d/18azadvf-9dqC39Ri-By6IiE_eUt2bu9rPX6WjRBjgic)
- [x] Testing complete

### Support FIPS mode on RHEL 7 and CentOS 7 (yanis) (api only)
* [Feature]()
* [API Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_fips_compliant.md)
- [ ] Testing complete

### Replace Celery with Dispatcher (jim) (api only)
* [Feature]()
* [API Test Plan](https://github.com/ansible/tower-qa/blob/devel/docs/test_plans/features/34_celery_replacement.md)
- [ ] Testing complete

### Settings Menu Reorganization (john) (ui only)
* [Feature]()
* [UI Test Plan](https://docs.google.com/document/d/1bZEUe6FW-gKY4y5tfcDdUwbRH2UdxxutMqZwYtww4lw)
- [ ] Testing complete

## Regression
1. [ ] UI regression completed
1. [ ] API regression completed - standalone
1. [ ] API regression completed - traditional cluster
1. [ ] API regression completed - OpenShift
1. [ ] Tower social authentication regression completed (vm)
   - [ ] Google OAuth
   - [ ] GitHub
   - [ ] GitHub Org
   - [ ] GitHub Team
   - [ ] Azure OAuth
   - [ ] Radius
1. [x] Tower SAML integration regression completed (vm)
1. [ ] Tower social authentication regression completed (OpenShift)
   - [ ] Google OAuth
   - [ ] GitHub
   - [ ] GitHub Org
   - [ ] GitHub Team
   - [ ] Azure OAuth
   - [ ] Radius
1. [x] Tower SAML integration regression completed (OpenShift)
1. [ ] Logging regression completed - standalone
1. [ ] Logging regression completed - cluster
1. [ ] Backup/restore successful - standalone
1. [ ] Backup/restore successful - traditional cluster (RHEL-7.5, Ubuntu-16)
1. [ ] Backup/restore successful - OpenShift

### Installation
Install/Deploy tower in the following configurations and validate functionality with automated tests

1. Installation completes successfully on all supported platforms (automated)
    * [ ] centos-7.latest
    * [ ] ubuntu-16.04
    * [ ] ol-7.latest
    * [ ] rhel-7.4
    * [ ] rhel-7.5
    * [ ] rhel-7.6
1. Installation completes successfully using supported ansible releases (automated)
    * [ ] devel
    * [ ] ansible-2.7
    * [ ] ansible-2.6
1. Cluster installation completes successfully on all supported platforms (automated)
    * [ ] centos-7.latest
    * [ ] ubuntu-16.04
    * [ ] ol-7.latest
    * [ ] rhel-7.4
    * [ ] rhel-7.5
    * [ ] rhel-7.6
1. Cluster installation completes successfully using supported ansible releases (automated)
    * [ ] devel
    * [ ] ansible-2.7
    * [ ] ansible-2.6
1. Bundled installation completes successfully on all supported platforms (automated)
    * [ ] centos-7.latest
    * [ ] ubuntu-16.04
    * [ ] ol-7.latest
    * [ ] rhel-7.4
    * [ ] rhel-7.5
    * [ ] rhel-7.6
1. [ ] Bundled installation completes successfully for clustered deployments
1. [ ] Deploy tower with [HTTPS+Load Balancer+Let's Encrypt](https://github.com/ansible/tower-qa/issues/1985)
1. [ ] Deploy tower in [OpenShift with an external DB](https://github.com/ansible/tower-qa/issues/1656)

### Upgrades for all supported platforms
1. [ ] Successful upgrades (and migrations) from `3.2.0` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.1` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.2` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.3` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.4` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.5` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.6` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.7` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.3.0` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.3.1` - `3.4.0` (standalone)
1. [ ] Successful upgrades (and migrations) from `3.2.0` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.2.1` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.2.2` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.2.3` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.2.4` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.2.5` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.2.6` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.2.7` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.3.0` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.3.1` - `3.4.0` (traditional cluster)
1. [ ] Successful upgrades (and migrations) from `3.3.0` - `3.4.0` (OpenShift)
1. [ ] Successful upgrades (and migrations) from `3.3.1` - `3.4.0` (OpenShift)
* Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant

### Misc

1. [ ] Archive result from the sign-off run and attach them in here.
