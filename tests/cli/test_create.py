import fauxfactory
import pytest

from tests.cli.utils import format_error


@pytest.mark.yolo
@pytest.mark.usefixtures('authtoken')
class TestObjectCreation(object):

    def test_missing_required_arguments(self, cli):
        result = cli(['awx', 'users', 'create'], auth=True)
        assert result.returncode == 2, format_error(result)

        assert (
            # https://github.com/python/cpython/commit/f97c59aaba2d93e48cbc6d25f7
            b'argument --username is required' in result.stdout or
            b'arguments are required: --username' in result.stdout
        )

        for arg in (
            b'--username TEXT', b'--first_name TEXT',
            b'--last_name TEXT', b'--email TEXT', b'--is_superuser BOOLEAN',
        ):
            assert arg in result.stdout

    def test_creation(self, cli, v2):
        username = fauxfactory.gen_alphanumeric()
        result = cli([
            'awx', 'users', 'create',
            '--username', username,
            '--password', 'secret'
        ], auth=True, teardown=True)
        assert result.returncode == 0, format_error(result)
        created = v2.users.get(username=username).results[0]
        assert result.json['id'] == created.id
        assert result.json['username'] == username

    def test_creation_with_extra_args(self, cli, v2):
        username = fauxfactory.gen_alphanumeric()
        result = cli([
            'awx', 'users', 'create',
            '--username', username,
            '--password', 'secret',
            '--first_name', 'Jane',
            '--last_name', 'Doe',
        ], auth=True, teardown=True)
        assert result.returncode == 0, format_error(result)
        created = v2.users.get(username=username).results[0]
        assert created.first_name == 'Jane'
        assert created.last_name == 'Doe'

    def test_creation_with_invalid_arguments(self, cli):
        username = 'x' * 1024
        result = cli([
            'awx', 'users', 'create',
            '--username', username,
            '--password', 'secret'
        ], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.json == {
            'username': ['Ensure this field has no more than 150 characters.']
        }
