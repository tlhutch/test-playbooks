import os

import pytest
from awxkit import config

from tests.cli.utils import format_error

class TestCLIBasics(object):

    @pytest.mark.parametrize('args', [
        ['awx'],
        ['awx', '-h'],
        ['awx', '--help'],
    ])
    def test_no_credentials(self, cli, args):
        # by default, awxkit will use localhost:8043,
        # which shouldn't be reachable in our CI environments
        result = cli(args)
        assert result.returncode == 1, format_error(result)
        assert b'usage: awx' in result.stdout

    def test_anonymous_user(self, cli):
        result = cli(['awx', '-k', '--conf.host', config.base_url])
        assert result.returncode == 0, format_error(result)

        # you can *see* endpoints without logging in
        for endpoint in (b'login', b'config', b'ping', b'organizations'):
            assert endpoint in result.stdout

    def test_credentials_required(self, cli):
        result = cli(['awx', 'me', '-k', '--conf.host', config.base_url])
        assert result.returncode == 1, format_error(result)
        assert b'Valid credentials were not provided.' in result.stdout
        assert b'$ awx login --help' in result.stdout

    def test_valid_credentials_from_env_vars(self, cli):
        username = config.credentials.users.admin.username
        result = cli(['awx', 'me'], env={
            'PATH': os.environ['PATH'],
            'TOWER_HOST': config.base_url,
            'TOWER_USERNAME': username,
            'TOWER_PASSWORD': config.credentials.users.admin.password,
            'TOWER_VERIFY_SSL': 'f',
        })
        assert result.returncode == 0, format_error(result)
        assert result.json['count'] == 1
        assert result.json['results'][0]['username'] == username

    def test_valid_credentials_from_cli_arguments(self, cli):
        username = config.credentials.users.admin.username
        result = cli([
            'awx', 'me',
            '-k', # SSL verify false
            '--conf.host', config.base_url,
            '--conf.username', username,
            '--conf.password', config.credentials.users.admin.password,
        ])
        assert result.returncode == 0, format_error(result)
        assert result.json['count'] == 1
        assert result.json['results'][0]['username'] == username

    def test_yaml_format(self, cli):
        result = cli(['awx', 'me', '-f', 'yaml'], auth=True)
        assert result.returncode == 0, format_error(result)
        assert result.yaml['count'] == 1
        assert result.yaml['results'][0]['username'] == config.credentials.users.admin.username  # noqa

    def test_human_format(self, cli):
        result = cli(['awx', 'me', '-f', 'human', '--filter', 'username'], auth=True)
        assert result.returncode == 0, format_error(result)
        assert result.stdout == b'==========\nusername\n==========\nadmin\n==========\n'

    def test_jq_custom_formatting(self, cli):
        result = cli(
            ['awx', 'me', '-f', 'jq', '--filter', '.results[].username'],
            auth=True
        )
        assert result.returncode == 0, format_error(result)
        assert result.stdout == bytes(
            config.credentials.users.admin.username,
            encoding='utf-8'
        ) + b'\n'

    def test_verbose_requests(self, cli):
        # -v should print raw HTTP requests
        result = cli(['awx', 'users', 'list', '-v'], auth=True)
        assert result.returncode == 0, format_error(result)
        assert b'"GET /api/v2/users/ HTTP/1.1" 200' in result.stdout

    def test_invalid_resource(self, cli):
        result = cli(['awx', 'taters'], auth=True)
        assert result.returncode == 2, format_error(result)
        assert b"resource: invalid choice: 'taters'" in result.stdout

    def test_invalid_action(self, cli):
        result = cli(['awx', 'users', 'bodyslam'], auth=True)
        assert result.returncode == 2, format_error(result)
        assert b"argument action: invalid choice: 'bodyslam'" in result.stdout

    def test_ping(self, cli):
        result = cli(['awx', 'ping'], auth=True)
        assert 'instances' in result.json

    def test_metrics(self, cli):
        result = cli(['awx', 'metrics'], auth=True)
        assert 'awx_system_info' in result.json
