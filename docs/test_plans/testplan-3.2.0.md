# Tower 3.2.0 Release Test Plan

## Resources
* 5 full-time automation engineers - cwang/jladd/jmcdermott/mfoord/rfitzpat

## Features Not Tested

## Features Tested

### OSS-ification: repo splits, build fixes, etc
[Feature](https://docs.google.com/document/d/11rZAP7oi7aE7ZfNYirjCqqXgtifnYDifnFRHFQRGWFs/edit)

1. [ ] ... 


### Headless Tower and ramparts packaging requirements
[Feature](https://docs.google.com/document/d/1r-Hf3JztX68R9X2dTUERcVG31LlgzLdfPaqXvkRNqeA/edit#)

1. [ ] ... 

### Instance Groups / External Ramparts
[Feature](https://drive.google.com/open?id=11G1Khsy8PUxAM8b8b0e5WxkiDUttI0tE72VrxfkGMcw)

When verifying acceptance we should ensure the following statements are true

1. [ ] Tower should install as a standalone Instance
1. [ ] Tower should install in a Clustered fashion
1. [ ] Instance should, optionally, be able to be grouped arbitrarily into different Instance Groups
1. [ ] Capacity should be tracked at the group level and capacity impact should make sense relative to what instance a job is running on and what groups that instance is a member of.
1. [ ] Provisioning should be supported via the setup playbook
1. [ ] De-provisioning should be supported via a management command
1. [ ] All jobs, inventory updates, and project updates should run successfully
1. [ ] Jobs should be able to run on hosts which it is targeted. If assigned implicitly or directly to groups then it should only run on instances in those Instance Groups.
1. [ ] Project updates should manifest their data on the host that will run the job immediately prior to the job running
1. [ ] Tower should be able to reasonably survive the removal of all instances in the cluster
1. [ ] Tower should behave in a predictable fashiong during network partitioning

#### Testing Considerations

1. [ ] Basic testing should be able to demonstrate parity with a standalone instance for all integration testing.
1. [ ] Basic playbook testing to verify routing differences, including:
    * [ ] Basic FQDN
    * [ ] Short-name name resolution
    * [ ] ip addresses
    * [ ] /etc/hosts static routing information
1. [ ] We should test behavior of large and small clusters. I would envision small clusters as 2 - 3 instances and large clusters as 10 - 15 instances
1. [ ] Failure testing should involve killing single instances and killing multiple instances while the cluster is performing work. Job failures during the time period should be predictable and not catastrophic.
1. [ ] Instance downtime testing should also include recoverability testing. Killing single services and ensuring the system can return itself to a working state
1. [ ] Persistent failure should be tested by killing single services in such a way that the cluster instance cannot be recovered and ensuring that the instance is properly taken offline
1. [ ] Network partitioning failures will be important also. In order to test this
    * [ ] Disallow a single instance from communicating with the other instances but allow it to communicate with the database
    * [ ] Break the link between instances such that it forms 2 or more groups where groupA and groupB can't communicate but all instances can communicate with the database.
1. [ ] Crucially when network partitioning is resolved all instances should recover into a consistent state
1. [ ] Upgrade Testing, verify behavior before and after are the same for the end user.
1. [ ] Project Updates should be thoroughly tested for all scm types (git, svn, hg) and for manual projects.
1. [ ] Setting up instance groups in two scenarios: a) instances are shared between groups b) instances are isolated to particular groups Organizations, Inventories, and Job Templates should be variously assigned to one or many groups and jobs should execute in those groups in preferential order as resources are available.

#### Performance Testing

Performance testing should be twofold:

1. [ ] Large volume of simultaneous jobs.
1. [ ] Jobs that generate a large amount of output.

These should also be benchmarked against the same playbooks using:
1. [ ] 3.0.3 Tower release, and 
1. [ ] a stable Ansible version. 

For a large volume playbook I might recommend a customer provided one that we've seen recently:

https://gist.github.com/michelleperz/fe3a0eb4eda888221229730e34b28b89

Against 100+ hosts.

### Insights integration 
[Feature](https://docs.google.com/document/d/1gpjGumL5SVCSqcJKTkkFTQGWAQ6vLUxn_NOrE75TMtk/edit)

1. [ ] ... 

### TACACS authentication 
[Feature](https://github.com/ansible/ansible-tower/issues/3400) (Jim)

1. [x] All specified Tower configuration fields should be shown and configurable as documented.
1. [x] User defined by TACACS+ server should be able to log in Tower.
1. [x] User not defined by TACACS+ server should not be able to log in Tower via TACACS+.
1. [x] A user existing in TACACS+ server but not in Tower should be created after the first success log in.
1. [x] TACACS+ backend should stop authentication attempt after configured timeout and should not block the authentication pipeline in any case.
1. [x] If exceptions occur on TACACS+ server side, the exception details should be logged in Tower, and Tower should not authenticate that user via TACACS+.
1. [ ] TACACS+ authentication cannot be used to login as a user initially created in tower

### Inventory UX 
[Feature](https://drive.google.com/open?id=1lvBf_Gf7peE4fucrdPUpRTMuTBz2SpS5Df273bd72Sk)

1. [ ] ... 

### Tower UX hitlist 
[Feature](https://docs.google.com/a/redhat.com/document/d/1Nvtn6ShHNS2jgEyjl79HelAEO8747Z5yj5QKh0sQ4VM/edit?usp=sharing_eil&ts=58b86ab9)

1. [ ] ... 

### Named URL access in API (slug) 
[Feature](https://docs.google.com/document/d/1dQObu1jV9zOz8FLlktipaySe9lbdT8-Jo99RL0bksok/edit)

1. [ ] ... 

### Arbitrary inventory/credential sources + Ansible 2.4 inventory 
[Feature](https://docs.google.com/document/d/1dQObu1jV9zOz8FLlktipaySe9lbdT8-Jo99RL0bksok/edit)

1. [ ] ... 

### SCM controlled static inventory 
[Feature](https://drive.google.com/open?id=1QCZDq0bgvkTu1udcskjn8NwxijTae9pbU_AMsA8Po84)

1. [ ] ... 

## Regression
1. [ ] UI regression completed
1. [ ] API regression completed
1. [ ] Tower HA installation regression completed
1. [ ] Tower LDAP Integration regression completed
1. [ ] Tower RADIUS Integration regression completed
1. [ ] Social authentication regression completed
1. [ ] Backup/restore successful

### Installation
1. Installation completes successfully on all supported platforms
    * [ ] ubuntu-14.04
    * [ ] ubuntu-16.04
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [ ] ansible-2.4 (devel branch)
    * [ ] ansible-2.3
    * [ ] ansible-2.2
    * [ ] ansible-2.1
1. Installation completes successfully on supported images
    * [ ] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [ ] rhel-7.latest
    * [ ] centos-7.latest
    * [ ] ol-7.latest

### Upgrades
1. [ ] Upgrade completes on all supported platforms from `3.1.*`
1. [ ] Verify the following functions work as intended after upgrade
    * [ ] Launch project_updates for existing projects
    * [ ] Launch inventory_updates for existing inventory_source
    * [ ] Launch, and relaunch, existing job_templates
    * [ ] Migrations were successful
