# Tower Applications and Access Tokens - Test Plan

### Feature Summary

Tower 3.4 introduces workflow level inventories, where users can set an
inventory to be used by any job template in the workflow that has "prompt on
launch" set.

### Related information
* [AWX Ticket](https://github.com/ansible/awx/issues/2256)
* [tower-qa ticket](https://github.com/ansible/tower-qa/issues/2209)

### Test case prerequisites

* Patch Towerkit for new feature [*towerkit PR*](https://github.com/ansible/towerkit/pull/487/)
  - [x] provide inventory to WFJT
  - [x] "prompt on launch" flag

### Test suites and cases
* [x] API
  * That workflow level inventory
    - [x] .. is not set, does not take effect
  * That workfow level inventory IS NOT applied if:
    - [x] .. the job has an inventory assigned and no “prompt on launch”
    - [x] .. the workflow JT has an inventory assigned and no “prompt on launch”
    - [x] .. If inventory is assigned to workflow, then deleted, that inventory is cleared, workflow can run, and deleted inventory has no effect on workflow
  * That workflow level inventory IS APPLIED
    - [x] .. if job is set to prompt for inventory (and doesn't have a default set)
        * Note: for a workflow job template node to be created, the job template needs to have an inventory at this time.
          The inventory is correctly applied if the job template's inventory is deleted after workflow node creation is completed, but
          the api disallows created a workflow job template node with a job template that has no inventory.
    - [x] .. if job is set to prompt for inventory (and does have a default set)
  * Other inventory items to consider:
    - [x] Source inventory with unicode name. Groups and hosts should have unicode names as well.
    - [x] Sourcing inventory without any hosts.
    - [x] Variation: Sourcing inventory with group(s), but no hosts.
    - [x] That variables (or any other data included in inventory) is also sourced during job run.
  * RBAC
    - [x] Users that have execute on the WFJT can provide inventories that they have the Use role for
    - [x] Users that have only "read" permissions on inventory cannot use them in WFJT
    - [x] Workflow JT Admin role is the only one that can set static inventory or “prompt on launch”
    - [x] That a user authorized to launch a workflow (but not assigned any permissions related to the inventory), can still launch the workflow (and that the workflow job is successful)

* [ ] [UI]()
