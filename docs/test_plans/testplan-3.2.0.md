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

### External Ramparts
[Feature](https://drive.google.com/open?id=11G1Khsy8PUxAM8b8b0e5WxkiDUttI0tE72VrxfkGMcw)

1. [ ] ... 

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
