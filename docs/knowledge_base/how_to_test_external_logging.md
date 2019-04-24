# Testing External Logging
This feature has yet to have automated testing added.
Historically, it has been sanity tested with one logging service.

Loggly is very simple to set up and provides a free trial so it is a good candidate.

Bugs related to external logging have been encountered. Here are some examples of past bugs:
https://github.com/ansible/tower/issues/3423
https://github.com/ansible/tower/issues/3141
https://github.com/ansible/tower/issues/1771

## Loggly
Reference docs: https://docs.ansible.com/ansible-tower/latest/html/administration/logging.html#loggly

### Manual testing:

1) create free account on loggly
2) select the http event source type
3) Copy the url that is of the form http://logs-01.loggly.com/inputs/TOKEN/tag/http/ in the "Configure Your App" portion
4) In tower, navigate to settings -> system -> logging
5) paste the URL you got from loggly into the "LOGGING AGGREGATOR" feild
6) Select the LOGGING AGGREGATOR TYPE as "Loggly"
7) Set LOGGING AGGREGATOR LEVEL THRESHOLD to DEBUG
7) Save
8) *** TOGGLE ENABLE EXTERNAL LOGGING TOGGLE ON TOP OF THIS PAGE! ***
8) SAVE AGAIN
8) "Test" the connection with "Test" button
9) Change time range on loggly view to be past 7 days because it is by default a very small time window
You should see an event like this show up:
```
2019-04-24 14:46:53.715
{ json: { @timestamp: "2019-04-24T18:46:53.581Z", level: "DEBUG", cluster_host_id: "ec2-3-87-197-66.compute-1.amazonaws.com", host: "ip-10-0-15-49.ec2.internal", logger_name: "awx", message: "AWX Connection Test", type: "loggly", tower_uuid: "c5fd798c-dc7b-4b43-b361-738be4ed8b6d" }, http: { clientHost: "3.87.197.66" } }

```
10) May have to keep fiddling with this time filter to see most recent events
9) Run job using `chatty_tasks.yml` and see that things should show up in loggly in standard view with no filters
10) Add filter for `json.logger_name:awx.analytics.job_events`. This can be done graphically or in search bar.
10) Note how many events are from the `job_events` logger
11) In tower, remove `job_events` from LOGGERS SENDING DATA
12) Run a job again and confirm that no new events arrive.
13) re-enable job_events, run a job, and confirm they arrive

## Splunk
Reference docs: https://docs.ansible.com/ansible-tower/latest/html/administration/logging.html#splunk

This seems to be a popular choice among customers, seem to get more bugs related to Splunk.

## Logstash
Reference docs: https://docs.ansible.com/ansible-tower/latest/html/administration/logging.html#elastic-stack-formerly-elk-stack
Good candidate for automation with provisioning on k8s
See:
  - https://github.com/ansible/tower/issues/3042#issuecomment-441819662
  - https://github.com/ITSvitCo/aws-k8s/blob/master/kubernetes-manifests/elasticsearch/logstash-application.yaml

Important thing to verify that we do not currently do is that the number of events that arrive are the same as the number of events in API.
Important to vary the size of the events -- it appears that large events may cause problems.
