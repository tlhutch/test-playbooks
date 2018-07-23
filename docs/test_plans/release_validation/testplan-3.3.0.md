# Tower 3.3.0 Release Test Plan

## Resources
* 5 full-time automation engineers - cwang/jladd/jhill/mfoord/rfitzpat

## Features Not Tested

## Features Tested

### Parameters for Scheduled and Workflow Jobs (cwang)
* [Feature](https://github.com/ansible/tower/blob/devel/docs/prompting.md)
* [Test Plan](https://docs.google.com/document/d/1M_W0g5gPo4kuuMwIcA5Z7BookbPID8PqxBwCuIIwS2Y/edit)

### Revise capacity algorithm (cwang)
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/capacity.md)
* [Test Plan](https://docs.google.com/document/d/1wr1IiwsP8pnZ-b-SiiQnh_jL_q4gtzOZQQN8oCvDi5s/edit)

### More granular permissions
* [Feature]()

### SAML/LDAP/etc hitlist catchall
* [Feature (saml)](https://github.com/ansible/tower/blob/release_3.3.0/docs/auth/saml.md)
* [Feature (ldap)](https://github.com/ansible/tower/blob/release_3.3.0/docs/auth/ldap.md)

### Update GCP credentials
* [Feature]()

### API-backed item copying
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/resource_copy.md)

### Multi-file support for Credential Types (cwang)
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/multi_credential_assignment.md)
* [Test Plan](https://docs.google.com/document/d/1haYuCGYGqPbiUqig4rJoDYyKfLHgCXm_yzXCeSxoiEo/edit)

### Pendo Opt-Out in License Screen
* [Feature]()

### Fact caching for isolated jobs (cwang)
* [Feature](https://github.com/ansible/awx/issues/198)
* [Test Plan](https://docs.google.com/document/d/1iddRSaS88L2bz10K1511PfKcDmVnm5M9LhqMh1ty6hE/edit)

### Containerized Tower as a product deliverable (cwang, jladd)
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/clustering.md)
* [Test Plan](https://docs.google.com/document/d/1qaLCCXoGEcAIW0Be-JTvBOM-KoC1AOGBju1nM9b3WbU/edit)

### Inventory & Network Visualization
* [Feature]()

### Token-based authentication to Tower
* [Feature (sessions)](https://github.com/ansible/tower/blob/release_3.3.0/docs/auth/session.md)
* [Feature (oauth)](https://github.com/ansible/tower/blob/release_3.3.0/docs/auth/oauth.md)

### Retry on Failed Hosts (guozhang)
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/retry_by_status.md)
* [Test Plan](https://docs.google.com/document/d/113A8f4j1_fUIZda2XArZ3kwHZVsOvIe8lcWrozd3oz4/edit?usp=sharing)

### Multiple venvs for ansible (jladd)
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/custom_virtualenvs.md)
* [Test Plan](https://docs.google.com/document/d/1TKkdj1pdeh9p048_S-sIMxSpAUKZuX3T65kcVKT8odM/edit)

### Multi-Credential (+ Multi-Vault) Assignment (jladd)
* [Feature](https://docs.google.com/document/d/1H5cphm39UFqV91nRiipNJxjlshpoBMwAIkx2n5cg2lQ/edit)
* [Test Plan](https://docs.google.com/document/d/1H5cphm39UFqV91nRiipNJxjlshpoBMwAIkx2n5cg2lQ/edit)

### Fix #823 (schedules timezone)
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/schedules.md)

### Event-ize all stdout + optimized multi-MB+ stdout + handle free/serial
* [Feature](https://github.com/ansible/tower/blob/release_3.3.0/docs/job_events.md)

## Regression
1. [ ] UI regression completed
1. [ ] API regression completed - standalone
1. [ ] API regression completed - traditional cluster
1. [ ] API regression completed - OpenShift cluster
1. [ ] Tower cluster installation regression completed
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
1. [ ] Installation completes successfully for cluster deployment (RHEL-7.4)
1. [ ] Bundled installation completes successfully for cluster deployment

### Upgrades
1. [ ] Successful migrations from `3.0.0` - `3.0.4`
1. [ ] Successful migrations from `3.1.0` - `3.1.5`
1. [ ] Successful upgrades on all supported platforms from `3.0.4` - standalone
1. [ ] Successful upgrades on all supported platforms from `3.1.5` - standalone
1. [ ] Successful upgrades on all supported platforms from `3.2.0` - `3.2.4` - standalone
1. [ ] Successful upgrades on all supported platforms from `3.2.0` - `3.2.4` - cluster

* Verify the following functionality after upgrade
    * Resource migrations
    * Launch project_updates for existing projects
    * Launch inventory_updates for existing inventory_source
    * Launch, and relaunch, existing job_templates

### Provided Images
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
