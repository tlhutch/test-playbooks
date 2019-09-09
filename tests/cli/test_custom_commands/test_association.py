import pytest


@pytest.mark.usefixtures('authtoken')
class TestCredentialAssociation(object):

    def test_jt_associate_missing_credential(self, cli, job_template_ping):
        result = cli([
            'awx', 'job_templates', 'associate', str(job_template_ping.id),
            '--credential', '999999999'
        ], auth=True)
        assert result.returncode == 1
        assert result.json['detail'] == 'Credential matching query does not exist.'
        assert job_template_ping.related.credentials.get().count == 1

    def test_duplicate_machine_credential(self, cli, job_template_ping):
        machine_cred = job_template_ping.related.credentials.get()['results'][0].id
        result = cli([
            'awx', 'job_templates', 'associate', str(job_template_ping.id),
            '--credential', str(machine_cred)
        ], auth=True)
        assert result.returncode == 1
        assert result.json['error'] == 'Cannot assign multiple Machine credentials.'

    @pytest.mark.parametrize('by', ('id', 'name'))
    def test_jt_credential(self, cli, job_template_ping, network_credential_with_ssh_key_data, by):
        assert job_template_ping.related.credentials.get().count == 1

        result = cli([
            'awx', 'job_templates', 'associate', str(getattr(job_template_ping, by)),
            '--credential', str(getattr(network_credential_with_ssh_key_data, by)),
        ], auth=True)
        assert result.json['count'] == 2
        assert job_template_ping.related.credentials.get().count == 2

        result = cli([
            'awx', 'job_templates', 'disassociate', str(getattr(job_template_ping, by)),
            '--credential', str(getattr(network_credential_with_ssh_key_data, by)),
        ], auth=True)
        assert result.json['count'] == 1
        assert job_template_ping.related.credentials.get().count == 1


@pytest.mark.usefixtures('authtoken')
class TestNotificationAssociation(object):

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    @pytest.mark.parametrize('by', ('id', 'name'))
    def test_jt_notification(self, cli, job_template_ping, webhook_notification_template,
                             param, related_endpoint, by):
        endpoint = getattr(job_template_ping.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'job_templates', action, str(getattr(job_template_ping, by)),
                '--{}'.format(param), str(getattr(webhook_notification_template, by))
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    @pytest.mark.parametrize('by', ('id', 'name'))
    def test_project_notification(self, cli, webhook_notification_template,
                             project_ansible_playbooks_git_nowait,
                             param, related_endpoint, by):
        endpoint = getattr(project_ansible_playbooks_git_nowait.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'projects', action, str(getattr(project_ansible_playbooks_git_nowait, by)),
                '--{}'.format(param), str(getattr(webhook_notification_template, by)),
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    @pytest.mark.parametrize('by', ('id', 'name'))
    def test_inventory_notification(self, cli, webhook_notification_template,
                                    inventory_source, param, related_endpoint,
                                    by):
        endpoint = getattr(inventory_source.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'inventory_sources', action, str(getattr(inventory_source, by)),
                '--{}'.format(param), str(getattr(webhook_notification_template, by))
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    @pytest.mark.parametrize('by', ('id', 'name'))
    def test_org_notification(self, cli, webhook_notification_template,
                              organization, param, related_endpoint, by):
        endpoint = getattr(organization.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'organizations', action, str(getattr(organization, by)),
                '--{}'.format(param), str(getattr(webhook_notification_template, by)),
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    @pytest.mark.parametrize('by', ('id', 'name'))
    def test_wfjt_notification(self, cli, webhook_notification_template,
                               workflow_job_template, param, related_endpoint,
                               by):
        endpoint = getattr(workflow_job_template.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'workflow_job_templates', action, str(getattr(workflow_job_template, by)),
                '--{}'.format(param), str(getattr(webhook_notification_template, by)),
            ], auth=True)
            assert endpoint.get().count == count
