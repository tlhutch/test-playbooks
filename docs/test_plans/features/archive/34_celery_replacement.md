Celery Replacement
------------------

see: https://github.com/ansible/tower/issues/2593

Tower 3.4 replaces our usage of celery with a homegrown task worker
implementation based on kombu.  This document describes the automated testing
requirements for the verification and final validation of this change.

At a minimum, before merging the celery replacement branch, we should see
runs of traditional, cluster, and OpenShift integration that run with
no clear outliers compared to release_3.3.0

We should also compare the runtimes of integration before and
*after* celery replacement to ensure that this change has not made Tower
notably slower.

In addition, the following are additional criteria for verification:

Single Node Cluster Failure Expectations
----------------------------------------
* If a job is running, and the database is unavailable for 60 seconds, the job
  should be marked as ERROR, and new job launches should succeed.
* If a job is running, and RabbitMQ is unavailable for 60 seconds, the job
  should be marked as ERROR, and new job launches should succeed.
* If a job is running, and Tower is stopped entirely (or the machine is
  hard-rebooted), the job should be marked as Failed (with an explanation)
  after Tower and the dispatcher come back online.
* If a job is running, and the *dispatcher* is stopped entirely, the job will
  continue to remain in running state (because there are no background workers
  to reap it), but you should be able to cancel it from the API.  When the
  dispatcher comes back online, the job should be reaped and marked as Failed.

Multinode Cluster Failure Expectations
--------------------------------------
In addition to single node cluster failure expectations:

* If a job is running on a node, and the node goes offline, other instances in
  the cluster should mark the node as having zero capacity, and all of its running
  jobs should immediately be marked as failed with an explanation.
* If a node is marked as being offline, any new jobs targeted to that node (via
  e.g., instance groups) should remain in pending state until the node comes back
  online.  In this scenario, the task manager logs should indicate the lack of
  capacity.
* If a job is running on one node, and the *dispatcher* on that node is stopped
  entirely, the job will continue to remain in running state until the node is
  marked as offline (capacity=0) by a peer.  While the job is stuck in running
  state, you should be able to cancel it from the API.

Explicit Feature Verification
-----------------------------
This should _mostly_ be covered by existing integration tests, though it would
be wise to make sure we have solid coverage for these features:

* Do scheduled jobs still work?
* Does cancellation for running jobs still work?
* Do instance heartbeats/capacity checks work for isolated and non-isolated
  cluster nodes?
* Does job reaping (as described above) work for jobs running on isolated nodes?
* Do settings changes still broadcast memcached cache clear jobs to all cluster
  nodes?

Additional RabbitMQ and Dispatcher-Specific Testing
--------------------------------------
* The dispatcher process has a pool of child processes that run jobs.  You can
  view what jobs are running on each worker using `awx-manage run_dispatcher --status`
  If a specific process is running a job, and it is sent either SIGKILL or
  SIGTERM, the job should be marked as failed, and a replacement worker should
  automatically be spawned.
* If you send SIGTERM or SIGKILL to *every* worker node in a pool, it should
  recover by spawning new child processes and be able to launch new jobs.
* If you send SIGTERM or SIGKILL to the *parent* dispatcher process, its child
  processes should gracefully exit within a reasonable timeframe (it should not
  leave behind orphaned processes).
* If you issue a notable number of tasks in *very* close proximity, is the
  dispatcher able to keep up and recover?

  from awx.main.tasks import cluster_node_heartbeat
  for _ in range(10000):
      cluster_node_heartbeat.apply_async()

  In this scenario, are you able to observe the pool of workers autoscale up to
  the max, and then back down to the minimum (by default, 4 workers)?
* RabbitMQ queues should _not_ grow in an unbounded way.  We can verify this by
  looking at the RabbitMQ Management web interface after an integration run and
  verifying there are no queues with accumulated unacked messages.
