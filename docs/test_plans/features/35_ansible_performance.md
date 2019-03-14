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
      * TBD on how that is going to happen
      * If on all the time, would be annoying with tons of info and cause database bloat
      * Default, OFF. useful for development and debugging
  * [ ] Stats can be collected separately for jobs running simultaneously on the same node
      * performance info is exclusive to the run
  * [ ] If enabled, venvs using an older version of ansible can still be used.
      * collect performance stats "if available"
  * [ ] Stats can be viewed as information on job events
      * stats will be associate with each job event
      * final job event will have summary information showing max cpu, max memory, etc.
  * [ ] Stats are collected for jobs on isolated nodes
  * [ ] Stats can be collected in an OpenShift deployment of tower
  * [ ] Jobs spawned by workflows or sliced jobs have stats
       * will be influenced how we choose to enable/disable stat collection
  * [ ] (Manual) verify that cpu/memory intensive jobs actually show spikes
 
* [ ] UI
  * [ ] TBD how do we let users decide to turn on/off in UI
  * [ ] Confirm STDOUT view does not freak out or redact desired output
