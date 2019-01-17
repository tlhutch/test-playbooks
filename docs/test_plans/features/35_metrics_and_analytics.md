# Metrics and Analytics

## Feature Summary

New metrics and analytics endpoints will be added to Tower for monitoring by Prometheus or similar timeseries tools.

* Analytics:
  * Anomalous tasks and hosts
  * Module Utilization
  * Time Savings with Automation
  * Federated view of Automation
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
  * [ ] Analytics
    * [ ] Module Utilization counts are accurate
      * [ ] Setup is excluded
      * [ ] Custom modules are included
    * [ ] Time Savings with automation is accurate based on inputs
    * [ ] Anomalous tasks
      * [ ] Are Reported
      * [ ] Can recover from this state
    * [ ] Anomalous Hosts
      * [ ] Are reported
      * [ ] Can recover from this state
    * [ ] RBAC
    * [ ] This feature can be disabled
  * [ ] Metrics
    * [ ] Counts are incremented correctly
    * [ ] Custom Modules are reported
    * [ ] Metrics are readable by
      * [ ] Prometheus
      * [ ] ???
    * [ ] RBAC
    * [ ] This feature can be disabled
