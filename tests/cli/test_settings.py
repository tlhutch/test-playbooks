import pytest


@pytest.mark.usefixtures('authtoken')
class TestSettingsCLI(object):

    def test_settings_list(self, cli, api_settings_system_pg):
        result = cli([
            'awx', 'settings', 'list', '-f', 'jq', '--filter', '.TOWER_URL_BASE'
        ], auth=True)
        assert result.stdout.decode('utf-8').strip() == api_settings_system_pg[
            'TOWER_URL_BASE'
        ]

    def test_settings_list_by_slug(self, cli):
        result = cli([
            'awx', 'settings', 'list', '--slug', 'system'
        ], auth=True)
        assert b'TOWER_URL_BASE' in result.stdout
        assert b'AWX_ISOLATED_VERBOSITY' not in result.stdout

    def test_settings_invalid_slug(self, cli):
        result = cli([
            'awx', 'settings', 'list', '--slug', 'bob'
        ], auth=True)
        assert result.returncode == 1
        assert result.json['detail'] == 'Not found.'

    def test_settings_update_missing_args(self, cli):
        result = cli(['awx', 'settings', 'modify'], auth=True)
        assert result.returncode == 2
        assert b'arguments are required: key, value' in result.stdout

    def test_invalid_key(self, cli, v2):
        result = cli([
            'awx', 'settings', 'modify', 'THINGAMAJIG', '1',
        ], auth=True)
        assert result.returncode == 2
        assert b"key: invalid choice: 'THINGAMAJIG' (choose from" in result.stdout

    @pytest.mark.parametrize('state', [True, False])
    def test_update_boolean(self, cli, v2, state):
        cli([
            'awx', 'settings', 'modify', 'INSIGHTS_TRACKING_STATE', str(state)
        ], auth=True)
        settings = v2.settings.get().get_endpoint('system')
        assert settings['INSIGHTS_TRACKING_STATE'] is state

    def test_update_integer(self, cli, v2):
        key = 'AWX_ISOLATED_VERBOSITY'
        v2.settings.get().get_endpoint('jobs').patch(key=0)
        cli([
            'awx', 'settings', 'modify', key, '1'
        ], auth=True)
        settings = v2.settings.get().get_endpoint('jobs')
        assert settings[key] == 1
        v2.settings.get().get_endpoint('jobs').patch(key=0)
