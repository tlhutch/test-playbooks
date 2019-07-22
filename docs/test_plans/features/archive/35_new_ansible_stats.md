# New Ansible Stats

## Feature Summary

Ansible Core 2.8 introduces two new statistics to the playbook summary: "Ignored" and "Rescued".

* Ignored - The task was a failure, but it is configured to ignore that and continue execution
* Rescued - The `rescue` section of a `block` was executed because a task has failed in the `block`.

## Related Information

* [AWX Ticket](https://github.com/ansible/awx/issues/466)

## Acceptance criteria

* [x] API
  * [x] Tasks with `ignore_errors: True` set are counted among the `ignored` by tower
  * [x] Tasks executed in a rescue block are counted among the `rescued` by tower
  * [x] Ignored tasks and Rescued tasks are accurately reflected in job host summaries
  * [x] Ignored tasks and Rescued tasks are accurately reflected in playbook_on_stats events

* [ ] Manual Verification
  * [ ] Passes an upgrade/migration test
  * [ ] (Manual) New stats are reflected in external logging
