import pytest

from tests.cli.utils import format_error


@pytest.mark.yolo
@pytest.mark.usefixtures('authtoken')
class TestSettingsCLI(object):

    def test_settings_list(self, cli, api_settings_system_pg):
        result = cli([
            'awx', 'settings', 'list', '-f', 'jq', '--filter', '.TOWER_URL_BASE'
        ], auth=True)
        assert result.stdout.strip() == api_settings_system_pg[
            'TOWER_URL_BASE'
        ]

    def test_settings_list_by_slug(self, cli):
        result = cli([
            'awx', 'settings', 'list', '--slug', 'system'
        ], auth=True)
        assert 'TOWER_URL_BASE' in result.stdout
        assert 'AWX_ISOLATED_VERBOSITY' not in result.stdout

    def test_settings_invalid_slug(self, cli):
        result = cli([
            'awx', 'settings', 'list', '--slug', 'bob'
        ], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.json['detail'] == 'Not found.'

    def test_settings_update_missing_args(self, cli):
        result = cli(['awx', 'settings', 'modify'], auth=True)
        assert result.returncode == 2, format_error(result)
        assert (
            # https://github.com/python/cpython/commit/f97c59aaba2d93e48cbc6d25f7
            'too few arguments' in result.stdout or
            'arguments are required: key, value' in result.stdout
        )

    def test_invalid_key(self, cli, v2):
        result = cli([
            'awx', 'settings', 'modify', 'THINGAMAJIG', '1',
        ], auth=True)
        assert result.returncode == 2, format_error(result)
        assert "key: invalid choice: 'THINGAMAJIG' (choose from" in result.stdout

    @pytest.mark.serial
    @pytest.mark.parametrize('state', [True, False])
    def test_update_boolean(self, cli, v2, state):
        cli([
            'awx', 'settings', 'modify', 'INSIGHTS_TRACKING_STATE', str(state)
        ], auth=True)
        settings = v2.settings.get().get_endpoint('system')
        assert settings['INSIGHTS_TRACKING_STATE'] is state

    @pytest.mark.serial
    def test_update_integer(self, cli, v2):
        key = 'AWX_ISOLATED_VERBOSITY'
        v2.settings.get().get_endpoint('jobs').patch(key=0)
        cli([
            'awx', 'settings', 'modify', key, '1'
        ], auth=True)
        settings = v2.settings.get().get_endpoint('jobs')
        assert settings[key] == 1
        v2.settings.get().get_endpoint('jobs').patch(key=0)

    @pytest.mark.serial
    def test_update_string(self, cli, v2):
        key = 'LOG_AGGREGATOR_TOWER_UUID'
        cli([
            'awx', 'settings', 'modify', key, 'some-random-value'
        ], auth=True)
        settings = v2.settings.get().get_endpoint('logging')
        assert settings[key] == 'some-random-value'
        v2.settings.get().get_endpoint('logging').patch(key='')

    @pytest.mark.serial
    def test_update_json(self, cli, v2):
        key = 'AWX_TASK_ENV'
        cli([
            'awx', 'settings', 'modify', key, '{"X_FOO": "bar"}'
        ], auth=True)
        settings = v2.settings.get().get_endpoint('jobs')
        assert settings[key] == {"X_FOO": "bar"}
        v2.settings.get().get_endpoint('jobs').patch(key='{}')

    def test_modify_settings_ldap(self, cli):
        """Test whether one can modify a list or dict setting from the awx command line tool.

        This test targets the following issue:

        https://github.com/ansible/awx/issues/5528
        """
        result = cli([
            'awx',
            'settings',
            'modify',
            'AUTH_LDAP_USER_SEARCH',
            r'["DC=ansible,DC=com","SCOPE_SUBTREE","(uid=%(user)s)"]'
        ], auth=True)
        assert result.json['key'] == 'AUTH_LDAP_USER_SEARCH'
        assert result.json['value'] == ['DC=ansible,DC=com', 'SCOPE_SUBTREE', '(uid=%(user)s)']
