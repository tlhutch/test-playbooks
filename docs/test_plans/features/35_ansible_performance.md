# Ansible Performance Statistics

## Feature Summary

This feature implements the cgroup-based ansible performance statistics plugin developed by Matt Martz (sivel).

This will gather resource usage information from playbook runs and store it in Tower. At this time no user-facing access is planned.

## Related Information

* [Tower Ticket](https://github.com/ansible/tower/issues/3223)
* [Ansible Core PR](https://github.com/ansible/ansible/pull/46346)

PRs:
* [awx](https://github.com/ansible/awx/pull/3609)
* [ansible-runner](https://github.com/ansible/ansible-runner/pull/246)
* [tower-packaging](https://github.com/ansible/tower-packaging/pull/294)
* [ansible](https://github.com/ansible/ansible/pull/54936) (merged)

## Acceptance criteria

* [ ] Ansible
    * [x] Patch merged to allow configuration of stats collection https://github.com/ansible/ansible/pull/54936/files

* [ ] Runner
  * [ ] Performance stats plugin can be whitelisted
       * [ ] Integration test for confirming performance stats show up in events

* [ ] API
  * [ ] This feature can be enabled and disabled using `AWX_PERF_STATS_ENABLED` field on `/api/v2/settings/jobs/` page
      * [ ] System setting for jobs at `api/v2/settings/jobs/`
	* [ ] Should default to off (to avoid overhead)
  * [ ] Profiling data can be collected separately for jobs running simultaneously on the same node
      * performance info is exclusive to the run
  * [ ] If enabled, venvs using an older version of ansible can still be used.
      * collect performance stats "if available"
  * [ ] Profiling data is shown in top-level `profiling_data` field of _detailed_ job event view. (Note: profiling_data field is omitted from job event list view so that it ran be rendered quickly).
      * final job event will have summary information showing max cpu, max memory, etc.
  * [ ] profiling_data field does not appear in job events for:
    * [ ] System Jobs
    * [ ] Workflow Jobs
  * [ ] Environment variables related to perfomance stats config are surfaced in JOB_ENV on job
  * [ ] Profiling data is collected for jobs on isolated nodes
  * [ ] Jobs spawned by workflows or sliced jobs have stats
       * will be influenced how we choose to enable/disable stat collection
  * [ ] (Manual) verify that cpu/memory intensive jobs actually show spikes
  * [ ] Enabling / disabling resource profiling should not affect actively running jobs

* [ ] UI
  * [ ] Users can enable / disable resource profiling using a toggle on the Job settings page
  * [ ] Confirm STDOUT view does not freak out or redact desired output

Feature should work on:
* [ ] RHEL 7 systems
* [ ] RHEL 8 systems
* [ ] Bundle installs
* [ ] RHEL Systems upgraded to 3.5

Note: Feature not currently supported on OpenShift or Ubuntu

## Additional Info

Executing the following commands on a tower host will enable resource profiling (and override any changes to settings via the REST API):

```
cat > /etc/tower/conf.d/perf_stats.py <<EOF
AWX_PERF_STATS_ENABLED = True
EOF
chown root:awx /etc/tower/conf.d/perf_stats.py
chmod 640 /etc/tower/conf.d/perf_stats.py
```
