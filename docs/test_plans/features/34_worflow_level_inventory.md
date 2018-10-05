# Tower Applications and Access Tokens - Test Plan

### Feature Summary

Tower 3.4 introduces workflow level inventories, where users can set an
inventory to be used by any job template in the workflow that has "prompt on
launch" set.

### Related information
* [AWX Ticket](https://github.com/ansible/awx/issues/2256)
* [tower-qa ticket](https://github.com/ansible/tower-qa/issues/2209)

### Test case prerequisites

    N/A

### Test suites and cases
* [x] API
  * That workflow level inventory
    - [ ] .. is not set, does not take effect
  * That workfow level inventory IS NOT applied if:
    - [x] .. the job has an inventory assigned and no “prompt on launch”
    - [x] .. the workflow JT has an inventory assigned and no “prompt on launch”
    - [ ] .. If inventory is assigned to workflow, then deleted, that inventory is cleared, workflow can run, and deleted inventory has no effect on workflow
  * That workflow level inventory IS APPLIED
    - [ ] .. if job is set to prompt for inventory (and doesn't have a default set)
    - [x] .. if job is set to prompt for inventory (and does have a default set)
  * That all possible types of inventories can be sourced
    - [ ] Static
    - [ ] SCM
    - [ ] Smart-inventory
    - [ ] Dynamic inventory
  * Other inventory items to consider:
    - [ ] Source inventory with unicode name. Groups and hosts should have unicode names as well.
    - [ ] Sourcing inventory without any hosts.
    - [ ] Variation: Sourcing inventory with group(s), but no hosts.
    - [ ] That variables (or any other data included in inventory) is also sourced during job run.
  * RBAC
    - [ ] Users that have execute on the WFJT can provide inventories that they have the Use role for
    - [x] Users that have only "read" permissions on inventory cannot use them in WFJT
    - [ ] Workflow JT Admin role is the only one that can set static inventory or “prompt on launch” 
    - [ ] That a user authorized to launch a workflow (but not assigned any permissions related to the inventory), can still launch the workflow (and that the workflow job is successful)
* [ ] [UI]()
