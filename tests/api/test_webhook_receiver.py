import pytest
import awxkit.exceptions
from awxkit import config
from awxkit.utils import poll_until
import requests
import json
from tests.api import APITest


def create_webhook_github(url, secret):
    """creates a github webhook for the resource"""
    username = config['credentials']['github']['username']
    token = config['credentials']['github']['token']
    hooks_url = 'https://api.github.com/repos/ansible/test-playbooks/hooks'
    gh_session = requests.Session()
    gh_session.auth = (username, token)
    payload = {"name": "web", "active": True, "events": ["push"],
               "config": {"url": url, "secret": secret, "content_type": "json", "insecure_ssl": "1"}}
    response = gh_session.post(hooks_url, data=json.dumps(payload), allow_redirects=False,
                               headers={'Content-type': 'application/json', 'Accept': 'application/json'})
    return response


def delete_webhook_github(id):
    """deletes the github webhook"""
    username = config['credentials']['github']['username']
    token = config['credentials']['github']['token']
    hook_url = 'https://api.github.com/repos/ansible/test-playbooks/hooks/' + str(id)
    gh_session = requests.Session()
    gh_session.auth = (username, token)
    response = gh_session.delete(hook_url)
    assert response.status_code == 204
    return response


def create_webhook_gitlab(url, secret):
    """creates a gitlab webhook for the resource"""
    hooks_url = "https://gitlab.com/api/v4/projects/14496406/hooks"
    querystring = {"url": url, "push_events": "true", "enable_ssl_verification": "false", "token": secret}
    payload = ""
    headers = {
        'Content-Type': "application/json",
        'PRIVATE-TOKEN': config['credentials']['gitlab']['token'],
        'Host': "gitlab.com",
    }
    response = requests.request("POST", hooks_url, data=payload, headers=headers, params=querystring, verify=False)
    return response


def delete_webhook_gitlab(id):
    """deletes the gitlab webhook"""
    hook_url = "https://gitlab.com/api/v4/projects/14496406/hooks/" + str(id)
    headers = {
        'PRIVATE-TOKEN': config['credentials']['gitlab']['token'],
        'Host': "gitlab.com",
    }
    response = requests.request("delete", hook_url, headers=headers)
    return response


@pytest.fixture
def jobs_triggered_by_github_webhook(request, factories, tower_baseurl, v2):
    """Create a JT/WFJT, create a webhook for the resource and then teardown the webhook
    after returning the job that was launched by the webhook ping event"""
    if not hasattr(request, 'param'):
        pytest.skip("no parameters")
    resource = request.param
    service = "github"
    if resource == 'job template':
        jt = factories.job_template()
    elif resource == 'workflow job template':
        jt = factories.workflow_job_template()
    jt.webhook_service = service
    url = tower_baseurl + str(jt.related.webhook_receiver)
    secret = str(jt.related.webhook_key.get().webhook_key)
    # Create Webhook
    response = create_webhook_github(url, secret)
    assert response.status_code == 201
    # Assert that the ping event launches the job (for github only) and return the job back
    if resource == 'job template':
        poll_until(lambda: v2.job_templates.get(id=jt.id).results.pop().related.jobs.get().count == 1, interval=5,
                   timeout=600)
        job = v2.job_templates.get(id=jt.id).results.pop().related.jobs.get()
    else:
        poll_until(
            lambda: v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get().count == 1,
            interval=5,
            timeout=600)
        job = v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get()
    yield job
    # Delete the created webhook by fetching the id from the response
    delete_webhook_github(response.json()['id'])


@pytest.fixture
def gitlab_webhook_creation_response(request, factories, tower_baseurl, v2):
    """Create a JT/WFJT, create a webhook for the resource and then teardown the webhook
    Note: gitlab does not send a ping event after webhook creation"""
    if not hasattr(request, 'param'):
        pytest.skip("no parameters")
    resource = request.param
    service = "gitlab"
    if resource == 'job template':
        jt = factories.job_template()
    elif resource == 'workflow job template':
        jt = factories.workflow_job_template()
    jt.webhook_service = service
    url = tower_baseurl + str(jt.related.webhook_receiver)
    secret = str(jt.related.webhook_key.get().webhook_key)
    # Create Webhook and yield the response
    response = create_webhook_gitlab(url, secret)
    yield response
    # Delete the created webhook by fetching the id from the response
    delete_webhook_gitlab(response.json()['id'])


@pytest.mark.usefixtures('authtoken')
class TestWebhookReceiver(APITest):
    """Test Webhook Receiver"""

    @pytest.mark.parametrize("service", ['github', 'gitlab'])
    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_basic_api(self, v2, factories, service, resource, github_credential, gitlab_credential):
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

        # Assert that if the webhook service is blanked out, the key and the receiver is unset too
        jt.webhook_service = ""
        assert jt.webhook_service == ""
        assert jt.related.webhook_key.get().webhook_key == ""
        assert jt.related.webhook_receiver == ""
        # Assert that webhook_service and webhook_credential can be provided while creating JT/WFJT
        another_jt = factories.job_template(webhook_service=service, webhook_credential=valid_credential)
        assert another_jt.webhook_service == service
        assert another_jt.webhook_credential == valid_credential.id

    @pytest.mark.parametrize('jobs_triggered_by_github_webhook', ['job template', 'workflow job template'], indirect=True)
    def test_webhook_config_github(self, jobs_triggered_by_github_webhook):
        """Test Webhook Configuration"""
        # get the jobs triggered after webhook creation on github
        jobs_triggered = jobs_triggered_by_github_webhook
        # Assert that a ping event sent after webhook creation launches the job
        assert len(jobs_triggered.results) == 1
        job = jobs_triggered.results.pop()
        assert job.extra_vars != ""
        assert job.webhook_service == "github"

    @pytest.mark.parametrize('gitlab_webhook_creation_response', ['job template', 'workflow job template'], indirect=True)
    def test_webhook_config_gitlab(self, gitlab_webhook_creation_response):
        """Test Webhook Configuration"""
        # get the jobs triggered after webhook creation on github
        response = gitlab_webhook_creation_response
        # Assert that the webhook is created, note that gitlab does not send a ping event to launch the job
        assert response.status_code == 201

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
