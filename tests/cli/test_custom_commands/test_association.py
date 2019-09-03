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

    def test_jt_credential(self, cli, job_template_ping, network_credential_with_ssh_key_data):
        assert job_template_ping.related.credentials.get().count == 1

        result = cli([
            'awx', 'job_templates', 'associate', str(job_template_ping.id),
            '--credential', str(network_credential_with_ssh_key_data.id)
        ], auth=True)
        assert result.json['count'] == 2
        assert job_template_ping.related.credentials.get().count == 2

        result = cli([
            'awx', 'job_templates', 'disassociate', str(job_template_ping.id),
            '--credential', str(network_credential_with_ssh_key_data.id)
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
    def test_jt_notification(self, cli, job_template_ping, webhook_notification_template,
                             param, related_endpoint):
        endpoint = getattr(job_template_ping.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'job_templates', action, str(job_template_ping.id),
                '--{}'.format(param), str(webhook_notification_template.id)
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    def test_project_notification(self, cli, webhook_notification_template,
                             project_ansible_playbooks_git_nowait,
                             param, related_endpoint):
        endpoint = getattr(project_ansible_playbooks_git_nowait.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'projects', action, str(project_ansible_playbooks_git_nowait.id),
                '--{}'.format(param), str(webhook_notification_template.id)
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    def test_inventory_notification(self, cli, webhook_notification_template,
                                    inventory_source, param, related_endpoint):
        endpoint = getattr(inventory_source.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'inventory_sources', action, str(inventory_source.id),
                '--{}'.format(param), str(webhook_notification_template.id)
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    def test_org_notification(self, cli, webhook_notification_template,
                              organization, param, related_endpoint):
        endpoint = getattr(organization.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'organizations', action, str(organization.id),
                '--{}'.format(param), str(webhook_notification_template.id)
            ], auth=True)
            assert endpoint.get().count == count

    @pytest.mark.parametrize('param, related_endpoint', [
        ['start_notification', 'notification_templates_started'],
        ['success_notification', 'notification_templates_success'],
        ['failure_notification', 'notification_templates_error'],
    ])
    def test_wfjt_notification(self, cli, webhook_notification_template,
                               workflow_job_template, param, related_endpoint):
        endpoint = getattr(workflow_job_template.related, related_endpoint)
        assert endpoint.get().count == 0
        for action, count in [['associate', 1], ['disassociate', 0]]:
            cli([
                'awx', 'workflow_job_templates', action, str(workflow_job_template.id),
                '--{}'.format(param), str(webhook_notification_template.id)
            ], auth=True)
            assert endpoint.get().count == count
