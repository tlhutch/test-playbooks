import os


class TestCLIConfig(object):

    def test_default_config(self, cli):
        result = cli(['awx', 'config'])
        assert result.returncode == 0
        assert result.json['base_url'] == 'https://127.0.0.1:443'
        assert result.json['token'] == ''
        assert result.json['credentials']['default']['username'] == 'admin'
        assert result.json['credentials']['default']['password'] == 'password'

    def test_config_from_cli_arguments(self, cli):
        result = cli([
            'awx', 'config',
            '--conf.host', 'https://awx.example.org',
            '--conf.username', 'test',
            '--conf.password', '123'
        ])
        assert result.returncode == 0
        assert result.json['base_url'] == 'https://awx.example.org'
        assert result.json['credentials']['default']['username'] == 'test'
        assert result.json['credentials']['default']['password'] == '123'

    def test_config_from_env_vars(self, cli):
        result = cli(['awx', 'config'], env={
            'PATH': os.environ['PATH'],
            'TOWER_HOST': 'https://awx.example.org',
            'TOWER_USERNAME': 'test',
            'TOWER_PASSWORD': '123',
        })
        assert result.returncode == 0
        assert result.json['base_url'] == 'https://awx.example.org'
        assert result.json['credentials']['default']['username'] == 'test'
        assert result.json['credentials']['default']['password'] == '123'
