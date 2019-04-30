import pytest

import towerkit
from towerkit.config import config
import towerkit.exceptions as exc

from tests.api import APITest


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestRelaunchAskRBAC(APITest):

    def give_user_relaunch_access(self, user, job):
        jt = job.related.job_template.get()
        jt.set_object_roles(user, 'execute')
        for dep in ['project', 'inventory']:
            if getattr(job, dep) != getattr(jt, dep):
                if dep == 'project':
                    jt.ds[dep].organization.set_object_roles(user, 'member')
                job.get_related(dep).set_object_roles(user, 'use')
        jt_creds = jt.get_related('credentials').results
        jt_cred_ids = [cred['id'] for cred in jt_creds]
        job_creds = job.get_related('credentials').results
        for cred in job_creds:
            if cred['id'] not in jt_cred_ids:
                cred.get_related('organization').set_object_roles(user, 'member')
                cred.set_object_roles(user, 'use')

    @pytest.fixture
    def relaunch_user(self, factories):
        return factories.v2_user()

    @pytest.fixture
    def relaunch_job_as_diff_user_forbidden(self, relaunch_user):
        def fn(job):
            '''
            Give user JT execute permission so that user doesn't get denied for
            reasons of RBAC instead of prompt relaunch permissions.
            '''
            self.give_user_relaunch_access(relaunch_user, job)
            with self.current_user(relaunch_user):
                with pytest.raises(towerkit.exceptions.Forbidden) as exc:
                    job.relaunch()
            assert 'Job was launched with secret prompts provided by another user.' == exc.value.msg['detail'], \
                "Failed while checking relaunch Permissions"
        return fn

    @pytest.fixture
    def relaunch_job_as_diff_user_allowed(self, relaunch_user):
        def fn(job):
            self.give_user_relaunch_access(relaunch_user, job)
            with self.current_user(relaunch_user):
                job.relaunch()
        return fn

    @pytest.mark.parametrize("patch_payload, launch_payload", [
        (dict(ask_limit_on_launch=True), dict(limit='local')),
        (dict(ask_tags_on_launch=True), dict(job_tags='test job_tag')),
        (dict(ask_skip_tags_on_launch=True), dict(skip_tags='test skip_tag')),
        (dict(ask_diff_mode_on_launch=True), dict(diff_mode=True)),
        (dict(ask_diff_mode_on_launch=True, diff_mode=True), dict(diff_mode=False)),
        (dict(ask_verbosity_on_launch=True, verbosity=1), dict(verbosity=0)),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=1)),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=2)),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=3)),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=4)),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=5)),
        (dict(ask_job_type_on_launch=True, job_type='check'), dict(job_type='run')),
        (dict(ask_job_type_on_launch=True), dict(job_type='check')),
        (dict(ask_variables_on_launch=True), dict(extra_vars=dict(foo='bar'))),
        (dict(), dict(skip_tags='test skip_tag', job_tags='test job_tag',
            diff_mode=True, job_type='check', verbosity=5, extra_vars=dict(foo='bar'),
            limit='foobar'))
    ], ids=['limit', 'job_tags', 'skip_tags', 'diff_mode on', 'diff mode off',
            '0-normal verbosity', '1-verbose', '2-more verbose', '3-debug verbosity',
            '4-connection debug verbosity', '5-winrm debug verbosity', 'job type run',
            'job type check', 'extra vars', 'noop']
    )
    def test_relaunch_with_payload(self, job_template, relaunch_job_as_diff_user_allowed, patch_payload, launch_payload):
        job_template.patch(**patch_payload)
        job = job_template.launch(launch_payload).wait_until_completed()
        relaunch_job_as_diff_user_allowed(job)

    @pytest.mark.parametrize("patch_payload, resource", [
        (dict(ask_inventory_on_launch=True), 'inventory'),
        (dict(ask_credential_on_launch=True), 'credential'),
    ])
    def test_relaunch_with_inventory_allowed(self, factories, job_template, relaunch_job_as_diff_user_allowed, patch_payload, resource):
        job_template.patch(**patch_payload)
        payload = dict()
        payload[resource] = getattr(factories, 'v2_' + resource)().id
        job = job_template.launch(payload).wait_until_completed()
        relaunch_job_as_diff_user_allowed(job)

    def test_relaunch_with_credentials_forbidden(self, v2, factories, job_template, relaunch_user, relaunch_job_as_diff_user_allowed):
        job_template.patch(ask_credential_on_launch=True)
        cloud_credentials = [factories.v2_credential(credential_type=factories.credential_type(),
                                                     user=relaunch_user,
                                                     organization=job_template.ds.project.organization) for i in [1, 2]]

        relaunch_creds = [c.id for c in cloud_credentials]
        relaunch_creds.append(job_template.ds.credential.id)
        job = job_template.launch(dict(credentials=relaunch_creds)).wait_until_completed()
        relaunch_job_as_diff_user_allowed(job)

    def test_relaunch_with_extra_credentials_forbidden(self, factories, relaunch_user, relaunch_job_as_diff_user_forbidden):
        """
        User with only execute role should not be able to relaunch a job for which
        `extra_credentials` were provided. This deprecated field cannot have its
        prompts re-applied since it does not use the up-to-date credential merging logic.
        """
        job_template = factories.v2_job_template(ask_credential_on_launch=True, credential=None)  # must be v2 type
        job_template.set_object_roles(relaunch_user, 'execute')
        cloud_credentials = [factories.v2_credential(credential_type=factories.credential_type(),
                                                     user=relaunch_user,
                                                     organization=job_template.ds.project.organization) for i in [1, 2]]
        cred_list = [c.id for c in cloud_credentials]

        with self.current_user(relaunch_user):
            job = job_template.launch(dict(extra_credentials=cred_list)).wait_until_completed()
            # Sanity check that credentials were actually used
            assert job.related.extra_credentials.get().count == 2

            with pytest.raises(towerkit.exceptions.Forbidden) as exc:
                job.relaunch()
        assert 'Job was launched with unknown prompted fields.' in exc.value.msg['detail'], \
            "Failed while checking relaunch Permissions"

    def test_relaunch_with_survey_passwords_forbidden(self, job_template, relaunch_job_as_diff_user_forbidden):
        survey = [dict(required=False, question_name='Test-1', variable='var1', type='password', default='var1_default')]
        job_template.add_survey(spec=survey)
        job = job_template.launch(dict(extra_vars=dict(var1='secret_foo'))).wait_until_completed()
        relaunch_job_as_diff_user_forbidden(job)

    def test_relaunch_with_no_ssh_password_provided_denied(self, factories, ssh_credential_ask):
        """Verify that relaunching a job w/ credential that has ask for password and password not provided
        results in no new job
        """
        jt = factories.v2_job_template(credential=ssh_credential_ask)

        job = jt.launch(dict(ssh_password=config.credentials.ssh.password)).wait_until_completed()
        with pytest.raises(exc.BadRequest) as e:
            job.relaunch()

        assert 'Missing passwords needed to start: ssh_password' in e.value.msg['credential_passwords']
        """one-off assertion to provide coverage for https://github.com/ansible/tower/issues/964
        A new job would be created even when access is denied.
        """
        assert jt.related.jobs.get(status='new').count == 0
