import pytest
import awxkit.exceptions
from awxkit import config
import time
import requests
import json
from tests.api import APITest
from urllib.parse import urlparse


@pytest.mark.usefixtures('authtoken')
class TestWebhookReceiver(APITest):
    """Test Webhook Receiver
    """

    def create_webhook_github(self, url, secret):
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

    def delete_webhook_github(self, id):
        """deletes the github webhook"""
        username = config['credentials']['github']['username']
        token = config['credentials']['github']['token']
        hook_url = 'https://api.github.com/repos/ansible/test-playbooks/hooks/' + str(id)
        gh_session = requests.Session()
        gh_session.auth = (username, token)
        response = gh_session.delete(hook_url)
        assert response.status_code == 204
        return response

    @pytest.mark.parametrize("service", ['github', 'gitlab'])
    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_basic_api(self, factories, service, resource):
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
            valid_credential = factories.credential(credential_type=12)
            invalid_credential = factories.credential(credential_type=13)
        else:
            valid_credential = factories.credential(credential_type=13)
            invalid_credential = factories.credential(credential_type=12)
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

    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_webhook_config(self, v2, factories, resource, tower_baseurl):
        """Test Webhook Configuration"""
        if resource == 'job template':
            jt = factories.job_template()
        else:
            jt = factories.workflow_job_template()
        jt.webhook_service = "github"
        url = tower_baseurl + str(jt.related.webhook_receiver)
        secret = str(jt.related.webhook_key.get().webhook_key)
        # Create Webhook
        response = self.create_webhook_github(url, secret)
        assert response.status_code == 201
        # Assert that the ping event launches the job
        time.sleep(5)
        if resource == 'job template':
            job = v2.job_templates.get(id=jt.id).results.pop().related.jobs.get()
        else:
            job = v2.workflow_job_templates.get(id=jt.id).results.pop().related.workflow_jobs.get()
        assert len(job.results) == 1
        job = job.results.pop()
        assert job.extra_vars != ""
        assert job.webhook_service == "github"
        # delete the webhook
        self.delete_webhook_github(response.json()['id'])

    @pytest.mark.parametrize("user_role",
                             ['sysadmin', 'jt_admin', 'system_auditor', 'org_executor', 'org_member', 'org_admin'])
    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_webhook_rbac(self, v2, factories, user_role, resource):
        """Test Webhook Key RBAC"""
        org = factories.organization()
        user = factories.user()
        if resource == 'job template':
            inv = factories.inventory(organization=org)
            project = factories.project(organization=org)
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
