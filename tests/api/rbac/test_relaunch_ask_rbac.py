import pytest

import towerkit

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestRelaunchAskRBAC(Base_Api_Test):

    def give_user_relaunch_access(self, user, job):
        jt = job.related.job_template.get()
        jt.set_object_roles(user, 'execute')
        for dep in ['credential', 'project', 'inventory']:
            if hasattr(jt.ds, dep):
                if dep == 'project':
                    jt.ds[dep].organization.set_object_roles(user, 'member')
                jt.ds[dep].set_object_roles(user, 'use')

    @pytest.fixture
    def relaunch_user(self, factories):
        return factories.v2_user()

    @pytest.fixture
    def relaunch_job_as_diff_user_forbidden(self, factories, relaunch_user):
        def fn(job):
            '''
            Give user JT execute permission so that user doesn't get denied for
            reasons of RBAC instead of prompt relaunch permissions.
            '''
            self.give_user_relaunch_access(relaunch_user, job)
            with self.current_user(relaunch_user):
                with pytest.raises(towerkit.exceptions.Forbidden) as exc:
                    job.relaunch()
            assert 'Job was launched with prompts provided by another user.' == exc.value.message['detail'], \
                "Failed while checking relaunch Permissions"
        return fn

    @pytest.fixture
    def relaunch_job_as_diff_user_allowed(self, factories, v2, relaunch_user):
        def fn(job):
            self.give_user_relaunch_access(relaunch_user, job)
            with self.current_user(relaunch_user):
                job.relaunch()
        return fn

    @pytest.mark.parametrize("patch_payload, launch_payload, deny", [
        (dict(ask_limit_on_launch=True), dict(limit='local'), True),
        (dict(ask_tags_on_launch=True), dict(job_tags='test job_tag'), True),
        (dict(ask_skip_tags_on_launch=True), dict(skip_tags='test skip_tag'), True),
        (dict(ask_diff_mode_on_launch=True), dict(diff_mode=True), True),
        (dict(ask_diff_mode_on_launch=True), dict(diff_mode=False), True),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=0), True),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=1), True),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=2), True),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=3), True),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=4), True),
        (dict(ask_verbosity_on_launch=True), dict(verbosity=5), True),
        (dict(ask_job_type_on_launch=True), dict(job_type='run'), True),
        (dict(ask_job_type_on_launch=True), dict(job_type='check'), True),
        (dict(ask_variables_on_launch=True), dict(extra_vars=dict(foo='bar')), True),
        (dict(), dict(skip_tags='test skip_tag', job_tags='test job_tag',
            diff_mode=True, job_type='check', verbosity=5, extra_vars=dict(foo='bar'),
            limit='foobar'), False)
    ], ids=['limit', 'job_tags', 'skip_tags', 'diff_mode on', 'diff mode off',
            '0-normal verbosity', '1-verbose', '2-more verbose', '3-debug verbosity',
            '4-connection debug verbosity', '5-winrm debug verbosity', 'job type run',
            'job type check', 'extra vars', 'noop']
    )
    def test_relaunch_with_payload(self, job_template, relaunch_job_as_diff_user_forbidden, relaunch_job_as_diff_user_allowed, patch_payload, launch_payload, deny):
        job_template.patch(**patch_payload)
        job = job_template.launch(launch_payload).wait_until_completed()
        if deny:
            relaunch_job_as_diff_user_forbidden(job)
        else:
            relaunch_job_as_diff_user_allowed(job)

    @pytest.mark.parametrize("patch_payload, resource", [
        (dict(ask_inventory_on_launch=True), 'inventory'),
        (dict(ask_credential_on_launch=True), 'credential'),
    ])
    @pytest.mark.parametrize("deny", ["True", "False"])
    def test_relaunch_with_inventory_forbidden(self, factories, job_template, relaunch_job_as_diff_user_forbidden, relaunch_job_as_diff_user_allowed, patch_payload, resource, deny):
        job_template.patch(**patch_payload)
        payload = dict()
        payload[resource] = getattr(factories, 'v2_' + resource)().id
        job = job_template.launch(payload).wait_until_completed()
        if deny:
            relaunch_job_as_diff_user_forbidden(job)
        else:
            relaunch_job_as_diff_user_allowed(job)

    @pytest.mark.github('https://github.com/ansible/tower/issues/867')
    def test_relaunch_with_credentials_forbidden(self, v2, factories, job_template, relaunch_user, relaunch_job_as_diff_user_forbidden):
        job_template.patch(ask_credential_on_launch=True)
        cloud_credentials = [factories.v2_credential(credential_type=factories.credential_type(),
                                                     user=relaunch_user,
                                                     organization=job_template.ds.project.organization) for i in [1, 2]]

        job = job_template.launch(dict(credentials=[c.id for c in cloud_credentials])).wait_until_completed()
        relaunch_job_as_diff_user_forbidden(job)

    @pytest.mark.github('https://github.com/ansible/tower/issues/1870')
    def test_relaunch_with_extra_credentials_forbidden(self, factories, job_template, relaunch_user, relaunch_job_as_diff_user_forbidden):
        job_template.patch(ask_credential_on_launch=True)
        cloud_credentials = [factories.v2_credential(credential_type=factories.credential_type(),
                                                     user=relaunch_user,
                                                     organization=job_template.ds.project.organization) for i in [1, 2]]
        job = job_template.launch(dict(extra_credentials=[c.id for c in cloud_credentials])).wait_until_completed()
        relaunch_job_as_diff_user_forbidden(job)
