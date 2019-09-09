import pytest

from tests.cli.utils import format_error


resources_action_and_keys = [
    ('users', 'list', ['id', 'username']),
    ('organizations', 'list', ['id', 'name']),
    ('projects', 'list', ['id', 'name']),
    ('teams', 'list', ['id', 'name']),
    ('credentials', 'list', ['id', 'name']),
    ('credential_types', 'list', ['id', 'name']),
    ('applications', 'list', ['id', 'name']),
    ('tokens', 'list', ['id', 'name']),
    ('inventory', 'list', [ 'id', 'name']),
    ('inventory_scripts', 'list', [ 'id', 'name']),
    ('inventory_sources', 'list', [ 'id', 'name']),
    ('groups', 'list', [ 'id', 'name']),
    ('hosts', 'list', [ 'id', 'name']),
    ('job_templates', 'list', [ 'id', 'name']),
    ('ad_hoc_commands', 'list', ['id', 'name']),
    ('schedules', 'list', ['id', 'name']),
    ('notification_templates', 'list', ['id', 'name']),
    ('labels', 'list', [ 'id', 'name']),
    ('workflow_job_templates', 'list', ['id', 'name']),
    ('workflow_job_template_nodes', 'list', ['id', 'name']),
    ('settings', 'list', ['key', 'value']),
    ('metrics', '', ['key', 'value']),
    ('me', '', ['id', 'username']),
    ('instances', 'list', ['id', 'hostname']),
]


@pytest.mark.usefixtures('authtoken')
class TestHumanDefaultFilters(object):

    @pytest.mark.parametrize('resource_action_and_keys',
        resources_action_and_keys,
        ids = [r[0] for r in resources_action_and_keys]
        )
    def test_human_default_filter(self, cli, resource_action_and_keys):
        resource, action, expected_keys = resource_action_and_keys
        result = cli(['awx', f'{resource}', f'{action}', '-f', 'human'], auth=True)
        assert result.returncode == 0, format_error(result)
        for key in expected_keys:
            assert key in result.stdout, format_error(result)
