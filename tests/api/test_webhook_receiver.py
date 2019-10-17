import pytest
import awxkit.exceptions
from awxkit import config
from awxkit.utils import poll_until
import requests
import json
from tests.api import APITest


def create_webhook_github(jt, tower_baseurl, github_credential):
    """creates a github webhook for the resource and returns the webhook id"""
    jt.webhook_service = "github"
    jt.webhook_credential = github_credential.id
    url = tower_baseurl + str(jt.related.webhook_receiver)
    secret = str(jt.related.webhook_key.get().webhook_key)
    username = config['credentials']['github']['username']
    token = config['credentials']['github']['token']
    hooks_url = 'https://api.github.com/repos/ansible/test-playbooks/hooks'
    gh_session = requests.Session()
    gh_session.auth = (username, token)
    payload = {"name": "web", "active": True, "events": ["push"],
               "config": {"url": url, "secret": secret, "content_type": "json", "insecure_ssl": "1"}}
    response = gh_session.post(hooks_url, data=json.dumps(payload), allow_redirects=False,
                               headers={'Content-type': 'application/json', 'Accept': 'application/json'})
    assert response.status_code == 201
    return response.json()['id']


def delete_webhook_github(id):
    """deletes the github webhook"""
    username = config['credentials']['github']['username']
    token = config['credentials']['github']['token']
    hook_url = 'https://api.github.com/repos/ansible/test-playbooks/hooks/' + str(id)
    gh_session = requests.Session()
    gh_session.auth = (username, token)
    response = gh_session.delete(hook_url)
    assert response.status_code == 204


def create_webhook_gitlab(jt, tower_baseurl):
    """creates a gitlab webhook for the resource and returns the webhook id"""
    jt.webhook_service = "gitlab"
    url = tower_baseurl + str(jt.related.webhook_receiver)
    secret = str(jt.related.webhook_key.get().webhook_key)
    hooks_url = "https://gitlab.com/api/v4/projects/14496406/hooks"
    querystring = {"url": url, "push_events": "true", "enable_ssl_verification": "false", "token": secret}
    payload = ""
    headers = {
        'Content-Type': "application/json",
        'PRIVATE-TOKEN': config['credentials']['gitlab']['token'],
        'Host': "gitlab.com",
    }
    response = requests.request("POST", hooks_url, data=payload, headers=headers, params=querystring, verify=False)
    assert response.status_code == 201
    return response.json()['id']


def delete_webhook_gitlab(id):
    """deletes the gitlab webhook"""
    hook_url = "https://gitlab.com/api/v4/projects/14496406/hooks/" + str(id)
    headers = {
        'PRIVATE-TOKEN': config['credentials']['gitlab']['token'],
        'Host': "gitlab.com",
    }
    response = requests.request("delete", hook_url, headers=headers)
    assert response.status_code == 204


@pytest.fixture
def resource_with_webhook_configured_on_github(request, factories, tower_baseurl, github_credential, v2):
    """Create a JT/WFJT, create a webhook for the resource and then teardown the webhook
    after returning the job that was launched by the webhook ping event"""
    if not hasattr(request, 'param'):
        pytest.skip("no parameters")
    resource = request.param
    # If resource is set to all, this fixtures returns both JT and WFJT that have webhook configured
    if resource == 'all':
        jt = factories.job_template()
        wfjt = factories.workflow_job_template()
        # Create Webhook
        id1 = create_webhook_github(jt, tower_baseurl, github_credential)
        id2 = create_webhook_github(wfjt, tower_baseurl, github_credential)
        yield jt, wfjt
        # Delete the webhook
        delete_webhook_github(id1)
        delete_webhook_github(id2)
    else:
        if resource == 'job template':
            jt = factories.job_template()
        elif resource == 'workflow job template':
            jt = factories.workflow_job_template()
        # Create Webhook
        id = create_webhook_github(jt, tower_baseurl, github_credential)
        yield jt
        # Delete the webhook
        delete_webhook_github(id)


@pytest.fixture
def resource_with_webhook_configured_on_gitlab(request, factories, tower_baseurl, v2):
    """Create a JT/WFJT, create a webhook for the resource and then teardown the webhook
    Note: gitlab does not send a ping event after webhook creation"""
    if not hasattr(request, 'param'):
        pytest.skip("no parameters")
    resource = request.param
    # If resource is set to all, this fixtures returns both JT and WFJT that have webhook configured
    if resource == 'all':
        jt = factories.job_template()
        wfjt = factories.workflow_job_template()
        # Create Webhook
        id1 = create_webhook_gitlab(jt, tower_baseurl)
        id2 = create_webhook_gitlab(wfjt, tower_baseurl)
        yield jt, wfjt
        # Delete the webhook
        delete_webhook_gitlab(id1)
        delete_webhook_gitlab(id2)
    else:
        if resource == 'job template':
            jt = factories.job_template()
        elif resource == 'workflow job template':
            jt = factories.workflow_job_template()
        # Create Webhook
        id = create_webhook_gitlab(jt, tower_baseurl)
        yield jt
        # Delete the webhook
        delete_webhook_gitlab(id)


@pytest.fixture
def push_event_response_github():
    """creates a push event to the repository and returns the response"""
    username = config['credentials']['github']['username']
    token = config['credentials']['github']['token']
    gh_session = requests.Session()
    gh_session.auth = (username, token)
    file_url = "https://api.github.com/repos/ansible/test-playbooks/contents/README.md?ref=webhook_test"
    sha = gh_session.get(file_url, data=json.dumps({"ref": "webhook_test"}), allow_redirects=False,
                              headers={'Content-type': 'application/json', 'Accept': 'application/json'})
    payload = {"message": "a new commit", "content": "bXkgdXBkYXRlZCBmaWxlIGNvbnRlbnRz", "sha": json.loads(sha.text)['sha'], "branch": "webhook_test"}
    response = gh_session.put(file_url, data=json.dumps(payload), allow_redirects=False,
                              headers={'Content-type': 'application/json', 'Accept': 'application/json'})

    return response


@pytest.fixture
def push_event_response_gitlab():
    """creates a push event to the repository and returns the response"""
    hooks_url = "https://gitlab.com/api/v4/projects/14496406/repository/files/README.md"
    querystring = {
      "commit_message": "a new commit message",
      "content": "bXkgdXBkYXRlZCBmaWxlIGNvbnRlbnRz",
      "branch": "webhook_test"
    }
    payload = ""
    headers = {
        'Content-Type': "application/json",
        'PRIVATE-TOKEN': config['credentials']['gitlab']['token'],
        'Host': "gitlab.com",
    }
    response = requests.request("PUT", hooks_url, data=payload, headers=headers, params=querystring, verify=False)
    return response


@pytest.mark.usefixtures('authtoken')
class TestWebhookReceiver(APITest):
    """Test Webhook Receiver"""

    @pytest.mark.parametrize("service", ['github', 'gitlab'])
    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_basic_api(self, factories, service, resource, github_credential, gitlab_credential):
        """Test the Basic API for Webhooks"""
        if resource == 'job template':
            jt = factories.job_template()
        else:
            jt = factories.workflow_job_template()
        # Assert that the webhook service, key and receiver is initially blank
        assert jt.webhook_service == ""
        assert jt.related.webhook_key.get().webhook_key == ""
        assert jt.related.webhook_receiver == ""
        # Assert that if webhook service is set, webhook key and the receiver endpoint is created
        jt.webhook_service = service
        assert jt.webhook_service == service
        assert jt.related.webhook_key.get().webhook_key != ""
        if resource == 'job template':
            assert jt.related.webhook_receiver == "/api/v2/job_templates/" + str(jt.id) + "/" + service + "/"
        else:
            assert jt.related.webhook_receiver == "/api/v2/workflow_job_templates/" + str(jt.id) + "/" + service + "/"
        assert jt.webhook_credential is None
        # Assert that any credential type other than the personal access token is not allowed
        if service == "github":
            valid_credential, invalid_credential = github_credential, gitlab_credential
        else:
            invalid_credential, valid_credential = github_credential, gitlab_credential
        with pytest.raises(awxkit.exceptions.BadRequest):
            jt.webhook_credential = invalid_credential.id
        # Assert that credential type of Access token can be set
        jt.webhook_credential = valid_credential.id
        assert jt.webhook_credential == valid_credential.id
        # Assert that the webhook service cannot be blanked out if the webhook_credential is set
        with pytest.raises(awxkit.exceptions.BadRequest):
            jt.webhook_service = ""
        # Assert that the webhook service can be blanked out if the webhook_credential is blank
        jt.webhook_credential = None
        jt.webhook_service = ""
        # Assert that if the webhook service is blanked out, the key and the receiver is unset too
        assert jt.webhook_service == ""
        assert jt.related.webhook_key.get().webhook_key == ""
        assert jt.related.webhook_receiver == ""
        # Assert that webhook_service and webhook_credential can be provided while creating JT/WFJT
        another_jt = factories.job_template(webhook_service=service, webhook_credential=valid_credential)
        assert another_jt.webhook_service == service
        assert another_jt.webhook_credential == valid_credential.id

    @pytest.mark.parametrize('resource_with_webhook_configured_on_github', ['job template', 'workflow job template'], indirect=True)
    def test_webhook_ping_event_github(self, v2, resource_with_webhook_configured_on_github):
        """Test that Webhook creation sends a ping event and the job is launched
        Note: If the tests give 422 "validation failed" error,
        it is because the repository can not have more than 20 push event webhooks,
        although this might not happen since we are deleting the webhook after the test,
        if it does, retry after deleting all hooks"""
        # creates a webhook for the resource and gets the specific resource which has webhooks enabled
        jt = resource_with_webhook_configured_on_github
        # Assert that the ping event launches the job (for github only)
        if jt.type == 'job_template':
            poll_until(lambda: v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().count == 1, interval=5,
                       timeout=600)
            jobs_triggered = v2.job_templates.get(id=jt.id).results.pop().related.jobs.get()
        else:
            poll_until(
                lambda: v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get().count == 1,
                interval=5,
                timeout=600)
            jobs_triggered = v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get()
        # Assert that a ping event sent after webhook creation launches the job
        assert len(jobs_triggered.results) == 1
        job = jobs_triggered.results.pop()
        assert job.extra_vars != ""
        assert json.loads(job.extra_vars)['tower_webhook_event_type'] == 'ping'
        job.wait_until_completed().assert_successful()
        assert job.webhook_service == "github"

    @pytest.mark.parametrize('resource_with_webhook_configured_on_github', ['job template', 'workflow job template'], indirect=True)
    def test_webhook_push_event_github(self, v2, resource_with_webhook_configured_on_github, push_event_response_github):
        """Test that after creation of webhook, any push event to the repository launches the specific job
        Note: If the tests give 422 "validation failed" error,
        it is because the repository can not have more than 20 push event webhooks,
        although this might not happen since we are deleting the webhook after the test,
        if it does, retry after deleting all hooks"""
        # creates a webhook for the resource and gets the specific resource which has webhooks enabled
        jt = resource_with_webhook_configured_on_github
        # Commit to the repository on which the webhook is configured
        assert push_event_response_github.status_code == 200
        # Assert that the push event launches the specific job
        # Expected count of jobs is 2 since one is launched by the ping event and one launched by the push event
        if jt.type == 'job_template':
            poll_until(lambda: v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().count == 2, interval=5,
                       timeout=600)
            job = v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().results.pop()
        else:
            poll_until(
                lambda: v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get().count == 2,
                interval=5,
                timeout=600)
            job = v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get().results.pop()
        # Assert the launched job details
        assert job.extra_vars != ""
        assert json.loads(job.extra_vars)['tower_webhook_event_type'] == 'push'
        assert job.webhook_service == "github"
        job.wait_until_completed().assert_successful()

    @pytest.mark.parametrize('resource_with_webhook_configured_on_gitlab', ['job template', 'workflow job template'], indirect=True)
    def test_webhook_push_event_gitlab(self, v2, resource_with_webhook_configured_on_gitlab, push_event_response_gitlab):
        """Test that after creation of webhook, any push event to the repository launches the specific job"""
        # creates a webhook for the resource and gets the specific resource which has webhooks enabled
        jt = resource_with_webhook_configured_on_gitlab
        # Commit to the repository on which the webhook is configured
        assert push_event_response_gitlab.status_code == 200
        # Assert that the push event launches the specific job
        # Expected count of jobs is 1 which is launched by the push event, ping event does not launch a job
        if jt.type == 'job_template':
            poll_until(lambda: v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().count == 1, interval=5,
                       timeout=600)
            jobs = v2.job_templates.get(id=jt.id).results.pop().related.jobs.get()
        else:
            poll_until(
                lambda: v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get().count == 1,
                interval=5,
                timeout=600)
            jobs = v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get()
        assert len(jobs.results) == 1
        job = jobs.results.pop()
        # Assert the launched job details
        assert job.extra_vars != ""
        assert json.loads(job.extra_vars)['tower_webhook_event_type'] == 'Push Hook'
        assert job.webhook_service == "gitlab"
        job.wait_until_completed().assert_successful()

    @pytest.mark.parametrize('resource_with_webhook_configured_on_github', ['all'], indirect=True)
    def test_webhook_on_multiple_resources_github(self, v2, resource_with_webhook_configured_on_github, push_event_response_github):
        """Test that if multiple resources have webhook enabled for the same repository on github, a push event launches all the relevant jobs"""
        # creates a webhook for both JT and WFJT that have webhooks configured on the same repository
        jt, wfjt = resource_with_webhook_configured_on_github
        # Commit to the repository on which the webhook is configured
        assert push_event_response_github.status_code == 200
        # Assert that the ping event and push event launches the all resources that have webhook enabled
        # Expected count of jobs is 2 since one is launched by the ping event and one launched by the push event
        poll_until(lambda: v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().count == 2, interval=5,
                   timeout=600)
        jt_job = v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().results.pop()
        poll_until(
            lambda: v2.workflow_job_templates.get(id=wfjt.id).results.pop().related.workflow_jobs.get().count == 2,
            interval=5,
            timeout=600)
        wfjt_job = v2.workflow_job_templates.get(id=wfjt.id).results.pop().related.workflow_jobs.get().results.pop()
        assert jt_job.extra_vars != ""
        assert json.loads(jt_job.extra_vars)['tower_webhook_event_type'] == 'push'
        jt_job.wait_until_completed().assert_successful()
        assert wfjt_job.extra_vars != ""
        assert json.loads(wfjt_job.extra_vars)['tower_webhook_event_type'] == 'push'
        wfjt_job.wait_until_completed().assert_successful()

    @pytest.mark.parametrize('resource_with_webhook_configured_on_gitlab', ['all'], indirect=True)
    def test_webhook_on_multiple_resources_gitlab(self, v2, resource_with_webhook_configured_on_gitlab, push_event_response_gitlab):
        """Test that if multiple resources have webhook enabled for the same repository on gitlab, a push event launches all the relevant jobs"""
        # creates a webhook for both JT and WFJT that have webhooks configured on the same repository
        jt, wfjt = resource_with_webhook_configured_on_gitlab
        # Commit to the repository on which the webhook is configured
        assert push_event_response_gitlab.status_code == 200
        # Assert that the ping event and push event launches the all resources that have webhook enabled
        # Expected count of jobs is 2 since one is launched by the ping event and one launched by the push event
        poll_until(lambda: v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().count == 1, interval=5,
                   timeout=600)
        jt_job = v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().results.pop()
        poll_until(
            lambda: v2.workflow_job_templates.get(id=wfjt.id).results.pop().related.workflow_jobs.get().count == 1,
            interval=5,
            timeout=600)
        wfjt_job = v2.workflow_job_templates.get(id=wfjt.id).results.pop().related.workflow_jobs.get().results.pop()
        assert jt_job.extra_vars != ""
        assert json.loads(jt_job.extra_vars)['tower_webhook_event_type'] == 'Push Hook'
        jt_job.wait_until_completed().assert_successful()
        assert wfjt_job.extra_vars != ""
        assert json.loads(wfjt_job.extra_vars)['tower_webhook_event_type'] == 'Push Hook'
        wfjt_job.wait_until_completed().assert_successful()

    @pytest.mark.parametrize("user_role",
                             ['sysadmin', 'jt_admin', 'system_auditor', 'org_executor', 'org_member', 'org_admin'])
    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_webhook_rbac(self, v2, factories, user_role, resource, project):
        """Test Webhook Key RBAC"""
        org = v2.organizations.get(id=project.organization).results.pop()
        user = factories.user()
        if resource == 'job template':
            inv = factories.inventory(organization=org)
            jt = factories.job_template(inventory=inv, project=project)
        else:
            jt = factories.workflow_job_template(organization=org)
        # Create User with appropriate permissions
        if user_role == 'sysadmin':
            user.is_superuser = True
        if user_role == 'system_auditor':
            user.is_system_auditor = True
        if user_role == 'org_admin':
            org.set_object_roles(user, 'admin')
        if user_role == 'org_executor':
            org.set_object_roles(user, 'execute')
        if user_role == 'jt_admin':
            jt.set_object_roles(user, 'admin')
        if user_role == 'org_member':
            org.set_object_roles(user, 'member')
        jt.webhook_service = "github"
        if resource == 'job template':
            assert jt.related.webhook_receiver == "/api/v2/job_templates/{}/github/".format(jt.id)
        else:
            assert jt.related.webhook_receiver == "/api/v2/workflow_job_templates/{}/github/".format(jt.id)
        with self.current_user(user.username, user.password):
            # Assert that valid users can access the webhook key
            if user_role in ['sysadmin', 'org_admin', 'jt_admin']:
                assert jt.related.webhook_key.get().webhook_key != ""
            # Assert that invalid users can not access the webhook key
            else:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    assert jt.related.webhook_key.get().webhook_key != ""
