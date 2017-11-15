# Tower 3.2.0 Release Test Plan

## Resources
* 5 full-time automation engineers - cwang/jladd/jmcdermott/mfoord/rfitzpat

## Features Not Tested

## Features Tested

### OSS-ification: repo splits, build fixes, etc
[Feature](https://docs.google.com/document/d/11rZAP7oi7aE7ZfNYirjCqqXgtifnYDifnFRHFQRGWFs/edit)

1. [x] Verify successful installations w/ tower-packaging split


### Headless Tower and ramparts packaging requirements
[Feature](https://docs.google.com/document/d/1r-Hf3JztX68R9X2dTUERcVG31LlgzLdfPaqXvkRNqeA/edit#)

1. [x] Verify successful instance group and isolated instance group installations w/ tower-packaging split

### Instance Groups / External Ramparts (Michael & Jim)
[Feature](https://drive.google.com/open?id=11G1Khsy8PUxAM8b8b0e5WxkiDUttI0tE72VrxfkGMcw)

When verifying acceptance we should ensure the following statements are true

1. [x] Tower should install as a standalone Instance
1. [x] Tower should install in a Clustered fashion
1. [x] Instances should, optionally, be able to be grouped arbitrarily into different Instance Groups
1. [x] Capacity should be tracked at the group level and capacity impact should make sense relative to what instance a job is running on and what groups that instance is a member of.
1. [x] Provisioning should be supported via the setup playbook
1. [x] De-provisioning should be supported via a management command
1. [x] All jobs, inventory updates, and project updates should run successfully
1. [x] Jobs should be able to run on hosts which it is targeted. If assigned implicitly or directly to groups then it should only run on instances in those Instance Groups.
1. [x] Project updates should manifest their data on the tower host that will run the job immediately prior to the job running
1. [x] Tower should be able to reasonably survive the removal of all instances in the cluster
1. [x] Tower should behave in a predictable fashion during network partitioning
1. [x] Users should not be able to assign instance groups to a job without the correct RBAC role

#### Testing Considerations

1. [x] Basic testing should be able to demonstrate parity with a standalone instance for all integration testing.
1. [x] Run existing integration tests verifying job (etc) behaviour, specifically targetting an isolated instance group.
1. [x] Basic setup playbook testing to verify routing differences, including:
    * [x] Basic FQDN
    * [x] Hostname
    * [ ] ~~Short-name name resolution~~ (really a duplicate of `/etc/hosts` routing)
    * [x] ip addresses
    * [x] /etc/hosts static routing information
1. [x] We should test behavior of large and small clusters. I would envision small clusters as 2 - 3 instances and large clusters as 10 - 15 instances
1. [x] Failure testing should involve killing single instances and killing multiple instances while the cluster is performing work. Job failures during the time period should be predictable and not catastrophic.
1. [x] Instance downtime testing should also include recoverability testing. Killing single services and ensuring the system can return itself to a working state
1. [x] Persistent failure should be tested by killing single services in such a way that the cluster instance cannot be recovered and ensuring that the instance is properly taken offline
1. [x] Network partitioning failures will be important also. In order to test this
    * [x] Disallow a single instance from communicating with the other instances but allow it to communicate with the database
    * [x] Break the link between instances such that it forms 2 or more groups where groupA and groupB can't communicate but all instances can communicate with the database.
1. [x] Crucially when network partitioning is resolved all instances should recover into a consistent state
1. [x] Upgrade Testing, verify behavior before and after are the same for the end user.
1. [x] Project Updates should be thoroughly tested for all scm types (git, svn, hg) and for manual projects.
1. [x] Setting up instance groups in two scenarios: a) instances are shared between groups b) instances are isolated to particular groups Organizations, Inventories, and Job Templates should be variously assigned to one or many groups and jobs should execute in those groups in preferential order as resources are available.

#### Performance Testing

Performance testing should be twofold:

1. [x] Large volume of simultaneous jobs.
1. [x] Jobs that generate a large amount of output.

These should also be benchmarked against the same playbooks using:
1. [x] 3.1.5 Tower release, and 
1. [x] a stable Ansible version. 

For a large volume playbook I might recommend a customer provided one that we've seen recently:

https://gist.github.com/michelleperz/fe3a0eb4eda888221229730e34b28b89

Against 100+ hosts.

### Host Filter (Chris)
[Feature](https://drive.google.com/open?id=1lvBf_Gf7peE4fucrdPUpRTMuTBz2SpS5Df273bd72Sk)

Filter functionality:
1. [x] Verify filter by host name functionality.
1. [x] Verify filter by group name functionality.
1. [x] Verify filter by `ansible_fact` functionality traversing lists.
1. [ ] Verify filter by `ansible_fact` functionality traversing dictionaries (AT-6015 and 6016 pushed out to 3.3.0).
1. [ ] Verify filter by `ansible_fact` functionality traversing nested lists and dictionaries (AT-6314 pushed out to 3.3.0).
1. [x] Verify two-part filters with OR operator.
1. [x] Verify two-part filters with AND operator.
1. [x] Verify three-part filters with a mix of boolean operators.
1. [x] Verify host_filter order of operations (parenthees support).
1. [x] Verify host_filter against unicode.
1. [x] Verify host_filter smart-search support.
1. [x] Verify proper handling of invalid `host_filter` requests.
1. [x] Verify host_filter performance.

RBAC:
1. [x] Host filter should return resources for which a user has inventory-read permissions.
1. [x] Host filter results are organization-scoped for organization admins.

### Set Facts (Chris)
[Feature](https://github.com/ansible/ansible-tower/blob/devel/docs/fact_cache.md)

Fact ingestion:
1. [x] `use_fact_cache` with gather_facts should update host `ansible_facts`.
1. [x] `use_fact_cache` without gather_facts should not update host `ansible_facts`.
1. [x] `use_fact_cache` with Tower scan modules should return expected facts.
1. [x] `use_fact_cache` updates host `ansible_facts` after each scan job.
1. [x] Host with spaces in hostname.
1. [x] Host with unicode hostname.

Fact use:
1. [x] Verify that facts may be used in a playbook within timeout window (`ANSIBLE_FACT_CACHE_TIMEOUT`).
1. [x] Verify that facts may not be used outside of timeout window (`ANSIBLE_FACT_CACHE_TIMEOUT`).'
1. [x] Verify fact use against multiple hosts.
1. [x] Verify fact use against simple host with JT limit.

Miscellaney:
1. [x] Verify fact ingestation and sourcing against all JSON data types.
1. [x] Verify fact cache ingestation and use over cluster.
1. [x] `clear_facts` should clear facts.

### Insights Integration (Chris)
[Feature](https://docs.google.com/document/d/1gpjGumL5SVCSqcJKTkkFTQGWAQ6vLUxn_NOrE75TMtk/edit)

1. [x] Verify stock value for host `insights_system_id`.
1. [x] Verify `insights_system_id` updates after scan job.
1. [x] Verify that `insights_system_id` is read-only.
1. [x] Verify inventory details update for Insights credential.
1. [x] Verify Insights credentials not allowed with smart inventories.
1. [x] Verify querying `/hosts/N/insights/` when host has no Insights credential.
1. [x] Verify querying `/hosts/N/insights/` when host has an Insights credential and is an Insights host.
1. [x] Verify querying `/hosts/N/insights/` when host has an Insights credential and is not an Insights host.
1. [x] Verify querying `/hosts/N/insights/` when host has an invalid Insights credential.
1. [x] Verify Insights project CRUD.
1. [x] Verify Insights project requires Insights credential as dependency.
1. [x] Verify Insights project update and downloaded playbooks.
1. [x] Verify Insights project update with invalid Insights credential.
1. [x] Verify Insights project update `.version` tag.
1. [x] Verify remediation JT run on target host.
1. [x] Perform end-to-end test of complete Insights flow.

### TACACS authentication (Jim)
[Feature](https://github.com/ansible/ansible-tower/issues/3400)

1. [x] All specified Tower configuration fields should be shown and configurable as documented.
1. [x] User defined by TACACS+ server should be able to log in Tower.
1. [x] User not defined by TACACS+ server should not be able to log in Tower via TACACS+.
1. [x] A user existing in TACACS+ server but not in Tower should be created after the first success log in.
1. [x] TACACS+ backend should stop authentication attempt after configured timeout and should not block the authentication pipeline in any case.
1. [x] If exceptions occur on TACACS+ server side, the exception details should be logged in Tower, and Tower should not authenticate that user via TACACS+.
1. [x] TACACS+ authentication cannot be used to login as a user initially created in tower

### Inventory UX
[Feature](https://drive.google.com/open?id=1lvBf_Gf7peE4fucrdPUpRTMuTBz2SpS5Df273bd72Sk)

Smart inventories (Chris):
1. [x] Verify smart inventory CRUD.
1. [x] Verify smart inventory host list updates for host edit.
1. [x] Verify smart inventory host list updates for host deletion.
1. [x] Verify smart inventory hosts reflects `host_filter`.
1. [x] Verify smart inventory `host_filter` is organization-scoped.
1. [x] Verify smart inventories group creation disallowed.
1. [x] Verify smart inventories host creation disallowed.
1. [x] Verify smart inventories inventory source creation disallowed.
1. [x] Verify smart inventories inventory update disallowed.
1. [x] Verify launching a job against a smart inventory.
1. [x] Verify launching an AHC against a smart inventory.
1. [x] Verify job launch with limit.
1. [x] Verify AHC launch with limit.
1. [x] Verify host update after job.
1. [x] Verify host update after AHC.
1. [x] Verify updating regular inventory into smart inventory.
1. [x] Verify updating smart inventory into regular inventory.
1. [x] Verify that only one host shows when duplicate hosts sourced.
1. [x] Verify source inventory variables ignored.
1. [x] Verify smart inventory variable precedence.
1. [x] Verify that smart inventory deletion does not cascade delete hosts.

RBAC (Chris):
1. [x] Verify inventory CRUD against all inventory permissions.
1. [x] Verify group CRUD against all inventory permissions.
1. [x] Verify host CRUD against all inventory permissions.
1. [x] Verify inventory source CRUD against all inventory permissions.
1. [x] Verify inv-admin against both smart and regular inventories.
1. [x] Verify inv-update against both smart and regular inventories.
1. [x] Verify inv-ahc against both smart and regular inventories.
1. [x] Verify inv-read against both smart and regular inventories.
1. [x] Verify inv-update against both smart and regular inventories.
1. [x] Verify inventory `user_capabilities` against all inventory permissions.
1. [x] Verify group `user_capabilities` against all inventory permissions.
1. [x] Verify host `user_capabilities` against all inventory permissions.
1. [x] Verify inventory source `user_capabilities` against all inventory permissions.

Inventory updates (Chris):
1. [x] Verify inventory updates via `/inventory_sources/N/update/`.
1. [x] Verify updating functional sources via `/inventories/N/update_inventory_sources/`.
1. [x] Verify updating functional and nonfunctional sources via `/inventories/N/update_inventory_sources/`.
1. [x] Verify updating nonfunctional sources via `/inventories/N/update_inventory_sources/`.
1. [x] Verify updating duplicate custom inventory sources via `/inventories/N/update_inventory_sources/`.
1. [x] Verify updating `/inventories/N/update_inventory_sources/` when no inventory sources present.
1. [x] Verify host and group promotion with `overwrite`.
1. [x] Verify default host and group behavior without `overwrite`.
1. [x] Verify variable overwrite with `overwrite_vars`.
1. [x] Verify default variable behavior without `overwrite_vars`.
1. [x] Verify inventory source `update_on_launch`.
1. [x] Verify inventory update verbosity.
1. [x] Test inventory update cascade deletion.

RBAC (Chris):
1. [x] Verify inventory update via `/inventory_sources/N/update/` against all inventory permissions.
1. [x] Verify inventory update via `/inventories/N/update_inventory_sources/` against all inventory permissions.
1. [x] Verify inventory update cancellation via all inventory permissions.
1. [x] Verify inventory update deletion via all inventory permissions.

Deprecated fields and v1 compatability (Jake)
1. [x] ....

Migrations (Jake)
1. [x] ....

### Tower UX hitlist 
[Feature](https://docs.google.com/a/redhat.com/document/d/1Nvtn6ShHNS2jgEyjl79HelAEO8747Z5yj5QKh0sQ4VM/edit?usp=sharing_eil&ts=58b86ab9)

1. [x] ... 

### Named URL access in API (slug) (Michael)
[Feature](https://docs.google.com/document/d/1dQObu1jV9zOz8FLlktipaySe9lbdT8-Jo99RL0bksok/edit)

1. [x] The classical way of getting objects via primary keys should behave the same.
1. [x] Tower configuration part of named URL should work as described. Particularly, `NAMED_URL_FORMATS` should be immutable on user side and display accurate named URL identifier format info.
1. [x] `NAMED_URL_FORMATS` should be exclusive, meaning resources specified in `NAMED_URL_FORMATS` should have named URL, and resources not specified there should *not* have named URL.
1. [x] If a resource can have named URL, its objects should have a `named_url` field which represents the object-specific named URL. That field should only be visible under detail view, not list view.
1. [x] A user following the rules specified in `NAMED_URL_FORMATS` should be able to generate named URL exactly the same as the `named_url` field.
1. [x] A user should be able to access specified resource objects via accurately generated named URL. This includes not only the object itself but also its related URLs, like if `/api/v2/res_name/obj_slug/` is valid, `/api/v2/res_name/obj_slug/related_res_name/` should also be valid.
1. [x] A user should not be able to access specified resource objects if the given named URL is inaccurate. For example, reserved characters not correctly escaped, or components whose corresponding foreign key field pointing nowhere is not replaced by empty string.
1. ~~~[ ] A user should be able to dynamically generate named URLs by utilizing `NAMED_URL_GRAPH_NODES`.~~~

### Arbitrary inventory/credential sources (Ryan)
[Feature](https://docs.google.com/document/d/1z6vW9W1yd0SbD46610XUr7WbNDDOg0jEAk8eETW-c8E)

1. [x] Verify continued v1 credential api support
1. [x] Verify managed-by-tower credential type content validity
1. [x] Verify managed-by-tower credential type sourced credential functionality
1. [x] Verify managed-by-tower credential types are read only
1. [x] Verify sourced custom credential types are read only
1. [x] Verify Credential Types activity stream history for basic object modification
1. [x] Verify SSH/Vault migration split
1. [x] Verify Rackspace migration
1. [x] Verify successful credential migrations
1. [x] Verify superuser has sole credential type creation ability
1. [x] Verify custom credential injection for jobs
1. [x] Verify custom credential injection for inventory updates
1. [x] Verify job with vault credential
1. [x] Verify job with extra credentials
1. [x] Verify job with vault and extra credentials

### SCM controlled inventory source + Ansible 2.4 inventory (Ryan)
[Feature](https://drive.google.com/open?id=1QCZDq0bgvkTu1udcskjn8NwxijTae9pbU_AMsA8Po84)

1. [x] Verify inventory sync including directory-provided host and group vars from static inventory file
1. [x] Verify inventory sync including directory-provided host and group vars from dynamic inventory file
1. [x] Verify desired inventory and yml files listed within project
1. [x] Verify undesired var files exluded from project inventory file list
1. [x] Verify dynamic inventory scripts use environment variables provided by custom credential
1. [x] Verify functionality of multiple inventory sources sharing a project with different source files.
1. [x] Verify file-related loading/syntax errors surface as inventory import failures
1. [x] Verify dynamic inventory script-related functional errors surface as inventory import failures
1. [x] Verify inventory sync attempt w/ update_on_project_update triggers project update
1. [x] Verify project update triggers inventory sync w/ update_on_project_update
1. [x] Verify update_on_project_update triggers project update and no inventory syncs on unaltered project
1. [x] Verify update_on_project_update triggers project update and inventory syncs on altered project
1. [x] Verify parent project update that encounters error doesn't trigger downstream inventory syncs
1. [x] Verify update_on_launch
1. [x] Verify overwrite

## Regression
1. [x] UI regression completed
1. [x] API regression completed
1. [x] Tower HA installation regression completed
1. [X] Tower LDAP Integration regression completed
1. [x] Tower RADIUS Integration regression completed
1. [x] Social authentication regression completed
1. [x] SAML authentication
1. [x] Verify logging (incl. cluster)
1. [x] Backup/restore successful

### Installation
1. Installation completes successfully on all supported platforms
    * [x] ubuntu-14.04
    * [x] ubuntu-16.04
    * [x] rhel-7.latest
    * [x] centos-7.latest
    * [x] ol-7.latest
1. Installation completes successfully using supported ansible releases
    * [x] ansible-2.4 (devel branch)
    * [x] ansible-2.3
    * [x] ansible-2.2
1. Installation completes successfully on supported images
    * [x] AMI (unlicensed)
    * [ ] Vagrant
1. Bundled installation completes successfully on all supported platforms (Automated)
    * [x] rhel-7.latest
    * [x] centos-7.latest
    * [x] ol-7.latest
1. [x] Bundled installation completes successfully for HA deployment

### Upgrades
1. [x] Upgrade completes on all supported platforms from `3.0.*`
1. [x] Upgrade completes on all supported platforms from `3.1.*`
1. [x] Verify the following functions work as intended after upgrade
    * [x] Launch project_updates for existing projects
    * [x] Launch inventory_updates for existing inventory_source
    * [x] Launch, and relaunch, existing job_templates
    * [x] Migrations were successful
