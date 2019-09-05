import pytest
from awxkit import exceptions

from tests.cli.utils import format_error


@pytest.mark.yolo
@pytest.mark.usefixtures('authtoken')
class TestObjectDeletion(object):

    def test_missing_primary_key(self, cli):
        result = cli(['awx', 'users', 'delete'], auth=True)
        assert result.returncode == 2, format_error(result)
        assert (
            # https://github.com/python/cpython/commit/f97c59aaba2d93e48cbc6d25f7
            'too few arguments' in result.stdout or
            'the following arguments are required: id' in result.stdout
        )

    def test_invalid_primary_key(self, cli):
        result = cli(['awx', 'users', 'delete', '99999999'], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.json['detail'] == 'Not found.'

    def test_valid_update(self, cli, anonymous_user):
        result = cli([
            'awx', 'users', 'delete', str(anonymous_user.id),
        ], auth=True)
        assert result.returncode == 0, format_error(result)
        with pytest.raises(exceptions.NotFound):
            anonymous_user.get()
