# Tower 3.3.0 Release Test Plan

## Resources
* 5 full-time automation engineers - cwang/jladd/jhill/mfoord/rfitzpat

## Features Not Tested

## Features Tested

### Parameters for Scheduled and Workflow Jobs
[Feature]()

### Enhanced isolated ansible-runner 
[Feature]()

### Revise capacity algorithm
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/capacity.md)

### More granular permissions
[Feature]()

### SAML/LDAP/etc hitlist catchall
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/auth/saml.md)

### Update GCP credentials
[Feature]()

### API-backed item copying
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/resource_copy.md)

### Multi-file support for Credential Types
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/multi_credential_assignment.md)

### Set up external translation infrastructure for AWX
[Feature]()

### Pendo Opt-Out in License Screen
[Feature]()

### Fact caching for isolated jobs
[Feature]()

### Containerized Tower as a product deliverable
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/clustering.md)

### "Ben's Stuff" - Inventory & Network Visualization
[Feature]()

### Token-based authentication to Tower
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/auth/session.md)
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/auth/oauth.md)

### CI and Test Suite for AWX
[Feature]()

### Retry on Failed Hosts
[Feature]()

### Multiple venvs for ansible
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/custom_virtualenvs.md)

### Automatic API docs generation
[Feature]()

### Change license enforcement
[Feature]()

### Fix #823 (schedules timezone)
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/schedules.md)

### Event-ize all stdout + optimized multi-MB+ stdout + handle free/serial
[Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/job_events.md)

### Idle connection restart handler
[Feature]()

### Update tower/awx-cli and tower/awx modules
[Feature]()

### XSS Tests
[Feature]()

### Django 1.11 / Celery 4.0
[Feature]()

### Angular update and similar housekeeping
[Feature]()

### Upgrade angular-ui-router
[Feature]()

### Update social-auth-core/social-app-django
[Feature]()

### Move to asgi_rabbitmq
[Feature]()

### Figure out source packaging for Tower
[Feature]()


## Regression
1. [ ] UI regression completed
1. [ ] API regression completed - standalone
1. [ ] API regression completed - traditional cluster
1. [ ] API regression completed - OpenShift cluster
1. [ ] Tower HA installation regression completed
1. [ ] Tower LDAP Integration regression completed
1. [ ] Tower RADIUS Integration regression completed
1. [ ] Social authentication regression completed
1. [ ] SAML authentication
1. [ ] Verify logging (incl. clusters)
1. [ ] Backup/restore successful

### Installation
1. Installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/requirements_refguide.html)
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.4 (latest)
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.7 (devel)
    * [ ] ansible-2.6
    * [ ] ansible-2.5
    * [ ] ansible-2.4
    * [ ] ansible-2.3
1. Bundled installation completes successfully on all [supported platforms](https://docs.ansible.com/ansible-tower/3.2.3/html/installandreference/tower_installer.html#bundled-install)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. [ ] Installation completes successfully for HA deployment (RHEL-7.2)
1. [ ] Bundled installation completes successfully for HA deployment

### Upgrades
1. [ ] Successful migrations from `3.0.0` - `3.0.4`
1. [ ] Successful migrations from `3.1.0` - `3.1.5`
1. [ ] Successful upgrades on all supported platforms from `3.0.4` - standalone
1. [ ] Successful upgrades on all supported platforms from `3.1.5` - standalone
1. [ ] Successful upgrades on all supported platforms from `3.2.0` - `3.2.4` - standalone
1. [ ] Successful upgrades on all supported platforms from `3.2.0` - `3.2.4` - HA

* Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
