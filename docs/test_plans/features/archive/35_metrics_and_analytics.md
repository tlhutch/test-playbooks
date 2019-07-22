# Metrics and Analytics

## Feature Summary

A new endpoint will be added to Tower for monitoring by Prometheus or similar timeseries tools.

Additionally, RHEL-based Tower installations will be able to upload metrics to Red Hat Insights.

* Metrics:
  * Job runs
    * Successful
    * Failed
  * Hosts
  * Job runs x hosts
  * Tasks x hosts
  * Job execution time
  * Task execution time
  * Module usage
  * User and team counts by org
  * Counts of
    * Projects
    * Job Templates
    * Workflow Job Templates
    * Credentials
  * Count by type
    * Inventory Source
    * Project
  * License usage
  * Count toplevel resources
  * Queue Length
    * Per-instance
    * Overall

## Related Information

* [AWX Ticket (Metrics)](https://github.com/ansible/awx/issues/1963)
* [Tower Ticket (Analytics)](https://github.com/ansible/tower/issues/3249)

## Acceptance criteria

* [ ] API
  * [ ] Red Hat Insights
    * [*] The tarball produced is valid and the data is valid JSON
    * [ ] Data can be consumed by insights
    * [*] Change to system state is reflected in data
    * [ ] Management task triggers as intended (manual observation)
    * [ ] Failure to push tarball is recoverable
    * [ ] Feature is not enabled on non-rhel platforms
  * [ ] Metrics
    * [ ] Counts are incremented correctly
    * [ ] Custom Modules are reported
    * [ ] Metrics are readable by
      * [ ] Prometheus
    * [ ] RBAC
    * [ ] This feature can be disabled
