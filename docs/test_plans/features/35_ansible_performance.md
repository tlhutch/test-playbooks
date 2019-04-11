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
  * [ ] profiling_data field is shown in detail view of the following types of job events:
    * [ ] `runner_on_ok`
    * [ ] `runner_item_on_ok`
    * [ ] `runner_on_failed`
    * [ ] `runner_item_on_failed`
    * [ ] TBD: `playbook_on_stats` --> This might include summary data
					Original test plan said "final job event will have summary information
					showing max cpu, max memory, etc."
  * [ ] Profiling data is shown in top-level `profiling_data` field of _detailed_ job event view for qualifying events.
  * [ ] Profiling data is NOT shown in list view of job events because of performance concerns of displaying in list view.
  * [ ] profiling_data field does not appear in job events for:
    * [ ] System Jobs
    * [ ] Workflow Jobs
  * [ ] Environment variables related to perfomance stats config are surfaced in JOB_ENV on job
  * [ ] Profiling data is collected for jobs on isolated nodes
  * [ ] Jobs spawned by workflows or sliced jobs have data collected
  * [ ] Enabling / disabling resource profiling should not affect actively running jobs
  * [ ] (Manual) verify that cpu/memory intensive jobs actually show spikes
	* [ ] (Manual) Create a test playbook and add to `ansible/test-playbooks` that
				has tasks that use `with_items` that take some amount of time for each
				item + perform some CPU intensive work for each task. Make both the
				length of time each item runs as well as the number of items
				configurable. This will generate many `runner_item_on_ok` events.
				 Test with and without performance data collection enabled.
				Graph results of runtime until `event_processing_finished` is true.
   * [ ] (Manual) Do same as above but instead of using `with_items` generate regular tasks which make `runner_on_ok` events.
   * [ ] (Manual) Enable external logging and observe if any problems with event size because of number of measurements on longer running tasks. (Related: https://github.com/ansible/tower/issues/3423 ) 

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

### How to enable setting for entire duration of a YOLO/SLOWYO run
Some settings tests revert settings to defaults, so it is important to make sure the performance data collection is actually enabled when running whole test suite.
Executing the following commands on a tower host will enable resource profiling (and override any changes to settings via the REST API):

```
cat > /etc/tower/conf.d/perf_stats.py <<EOF
AWX_PERF_STATS_ENABLED = True
EOF
chown root:awx /etc/tower/conf.d/perf_stats.py
chmod 640 /etc/tower/conf.d/perf_stats.py
```

### Inspecting events in database
While in API `profiling_data` is filtered from some events in api results, all events actually do have this feild in the database.
To select job events associated with a job you can do something like this on a tower box through `awx-manage dbshell`:

```
 SELECT event, LEFT(profiling_data, <char length of profile data to allow>) FROM main_jobevent WHERE job_id=<job id of interest> AND profiling_data != '{}';
```

### Data is not allways collected

_NOTE_ because data is only collected every so often (at writing every
0.25 seconds), sometimes no data will be collected. Instead of an empty
dictionary, though, we should see a dictionary with the data keys but
with empty lists of measurements such as: `{"cpu": [], "memory": [], "pids": []} `
