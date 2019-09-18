import pytest
import awxkit.exceptions
from awxkit.utils import poll_until
from awxkit import config
import time
import requests
import json
from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestWebhookReceiver(APITest):
    """Test Webhook Receiver
    """

    def create_webhook_github(self, url, secret):
        """creates a github webhook for the resource"""
        username = 'appuk'
        # from https://github.com/user/settings/tokens
        token = 'e1f664f727e68a5a75505ea79cde01f24c08f46d'
        repos_url = 'https://api.github.com/repos/appuk/test-playbooks/hooks'
        gh_session = requests.Session()
        gh_session.auth = (username, token)
        payload = {"name": "web", "active": True, "events": ["push"],
                   "config": {"url": url, "secret": secret, "content_type": "json", "insecure_ssl": "1"}}
        return gh_session.post(repos_url, data=json.dumps(payload), allow_redirects=False,
                               headers={'Content-type': 'application/json', 'Accept': 'application/json'})

    def create_webhook_gitlab(self, url, secret):
        """creates a gitlab webhook for the resource"""
        hooks_url = "https://gitlab.cee.redhat.com/api/v4/projects/23273/hooks"
        querystring = {"url": url, "push_events": "true", "enable_ssl_verification": "false", "token": secret}
        payload = ""
        headers = {
            'Content-Type': "application/json",
            'PRIVATE-TOKEN': "3oRCFQw-sMLcb1BxcwNR",
            'Accept': "*/*",
            'Cache-Control': "no-cache",
            'Host': "gitlab.cee.redhat.com",
            'Accept-Encoding': "gzip, deflate",
            'Content-Length': "0",
            'Connection': "keep-alive",
        }
        return requests.request("POST", hooks_url, data=payload, headers=headers, params=querystring, verify=False)

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
        # assert jt.webhook_credential == None

        # Assert that the webhook service and credential can be set while creating the JT/WFJT
        another_jt = factories.job_template(webhook_service=service, webhook_credential=valid_credential)

    @pytest.mark.parametrize("service", ['github', 'gitlab'])
    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_webhook_config(self, v2, factories, service, resource):
        """Test Webhook Configuration"""
        if resource == 'job template':
            jt = factories.job_template()
        else:
            jt = factories.workflow_job_template()
        jt.webhook_service = "github"
        url = config.base_url + str(jt.related.webhook_receiver)
        secret = str(jt.related.webhook_key.get().webhook_key)
        # Create Webhook    
        if service == "gitlab":
            assert self.create_webhook_gitlab(url, secret).status_code == 201
        else:
            assert self.create_webhook_github(url, secret).status_code == 201
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

    @pytest.mark.parametrize("user_role",
                             ['sysadmin', 'jt_admin', 'system_auditor', 'org_executor', 'org_member', 'org_admin'])
    @pytest.mark.parametrize("resource", ['job template', 'workflow job template'])
    def test_webhook_rbac(self, v2, factories, user_role, resource):
        """Test Webhook Key RBAC"""
        valid_users = ['sysadmin', 'org_admin', 'jt_admin']
        org = factories.organization()
        user = factories.user()
        if resource == 'job template':
            jt = factories.job_template(organization=org)
        else:
            jt = factories.workflow_job_template(organization=org)
        if user_role == 'sysadmin':
            user.is_superuser = True
        if user_role == 'system_auditor':
            user.is_system_auditor = True
        if user_role == 'org_admin':
            org.set_object_roles(user, 'admin')
        if user_role == 'org_executor':
            org.set_object_roles(user, 'execute')
        jt.webhook_service = "github"
        if user_role == 'jt_admin':
            jt.set_object_roles(user, 'admin')
        if user_role == 'org_member':
            org.set_object_roles(user, 'member')
        assert jt.webhook_service == "github"
        assert jt.related.webhook_receiver == "/api/v2/job_templates/{}/github/".format(jt.id)
        with self.current_user(user.username, user.password):
            # Assert that valid users can access the webhook key    
            if user_role in valid_users:
                assert jt.related.webhook_key.get().webhook_key != ""
            # Assert that invalid users can not access the webhook key    
            else:
                with pytest.raises(awxkit.exceptions.Forbidden):
                    assert jt.related.webhook_key.get().webhook_key != ""
