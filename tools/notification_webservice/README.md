Notification Webservice
=======================

The notification webservice receives and stores requests from Tower's webhook notifications. [Notification tests](https://github.com/ansible/tower-qa/blob/master/tests/api/test_notifications.py) generate webhook notifications and use a [library](https://github.com/ansible/towerkit/blob/master/towerkit/notification_services.py) to confirm the requests were received and have the expected content.

# Files

* `app.yml` - service metadata (e.g. version)
* `notification_service.py` - source code for webservice

# To install the notification webservice:
If using an existing Google Cloud project, skip to the steps below, otherwise:
 - Open Google Cloud console and create new project (https://console.cloud.google.com)
 - Will need to enable billing for project as well. Under main menu (top-left corner), click Billing.

1. Install Google Cloud SDK (https://cloud.google.com/sdk/docs/)
2. `gcloud init`  # Login with redhat.com e-mail
3. `cd` to directory containing webservice files (`app.yml` and `notification_service.yml`)
3. `gcloud app deploy`
4. When command finishes, will give location of service (e.g. https://ansible-tower-engineering.appspot.com)

# Getting credentials for python api (gcloud):
1. Open Google Cloud's console: https://console.cloud.google.com
2. Click on navigation menu (three horizontal bars, top-left corner)
3. Open IAM & Admin
4. Open Service accounts
5. Create a service account if needed. Beside account, click three dots, select Create key. Select JSON.
6. Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable to the path of the JSON file downloaded.
For more information, see https://developers.google.com/identity/protocols/application-default-credentials

# To provide jenkins with the api key:
1. Open the configuration page for your job.
2. Under the Bindings section, click add and select Secret file.
3. Set Variable to `GOOGLE_APPLICATION_CREDENTIALS`
4. Under Credentials, select Specific credentials. Click to add a credentials file. 

# Configuring tests:

If `tests/credentials.txt` already exists, include the following section:

```shell
notification_services:
  webhook:
    gce_body_field: request_body
    gce_parent_key: LogEntry
    gce_project: ansible-tower-engineering                    <--- change to project name
    url: https://ansible-tower-engineering.appspot.com        <--- change to url shown by `gcloud app deploy`
    gce_headers_field: headers
```

If `tests/credentials.txt` is generated using `scripts/create_credentials.py`, set the following environment variables:

```shell
* WEBHOOK_BODY_FIELD=request_body
* WEBHOOK_PARENT_KEY=LogEntry
* WEBHOOK_PROJECT=ansible-tower-engineering                   <--- change to project name
* WEBHOOK_URL=https://ansible-tower-engineering.appspot.com   <--- change to url shown by `gcloud app deploy`
* WEBHOOK_HEADERS_FIELD=headers
```

# To view logs from service:
1. Open Google Cloud's console: https://console.cloud.google.com
2. Click on navigation menu (three horizontal bars, top-left corner)
3. Under Storage, click Datastore
4. Can sort table shown by date to see most recent log entry.

# To disable service:
1. Open Google Cloud's console: https://console.cloud.google.com
2. Click on navigation menu (three horizontal bars, top-left corner)
3. Under Compute, click on App Engine
4. On menu at left, click on Settings
5. Click Disable application (type project name, shown in modal)

Note: Have not found an easy way to delete a service (Google requires a replacement):
http://stackoverflow.com/questions/37679552/cannot-delete-version

# Reference

Google App Engine:
https://cloud.google.com/appengine/docs/python/

Google Cloud API:
https://github.com/GoogleCloudPlatform/google-cloud-python
https://google-cloud-python.readthedocs.io/en/latest/google-cloud-auth.html  # Authentication
https://developers.google.com/identity/protocols/application-default-credentials  # Default credentials 

Datastore API:
https://cloud.google.com/datastore/docs/#apis--reference  # Quick start
