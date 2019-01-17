# Ansible Performance Statistics

## Feature Summary

This feature implements the cgroup-based ansible performance statistics plugin developed by Matt Martz (sivel).

This will gather resource usage information from playbook runs and store it in Tower. At this time no user-facing access is planned.

## Related Information

* [Tower Ticket](https://github.com/ansible/tower/issues/3223)
* [Ansible Core PR](https://github.com/ansible/ansible/pull/46346)

## Acceptance criteria

* [ ] API
  * [ ] This feature can be enabled and disabled
  * [ ] Stats can be collected separately for jobs running simultaneously on the same node
  * [ ] If enabled, venvs using an older version of ansible can still be used.
  * [ ] Stats can be viewed at the api endpoint for the job
  * [ ] Stats endpoint can be accessed while a job is running
  * [ ] Stats endpoint is not available on
    * [ ] System Jobs
    * [ ] Workflow Jobs
  * [ ] Stats are collected for jobs on isolated nodes
  * [ ] Stats can be collected in an OpenShift deployment of tower
  * [ ] Jobs spawned by workflows or sliced jobs have stats
  * [ ] Stats are removed by cleanup jobs
  * [ ] (Manual) verify that cpu/memory intensive jobs actually show spikes