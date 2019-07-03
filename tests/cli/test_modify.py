import pytest


@pytest.mark.usefixtures('authtoken')
class TestObjectModification(object):

    def test_missing_primary_key(self, cli):
        result = cli(['awx', 'users', 'modify'], auth=True)
        assert result.returncode == 2
        assert b'the following arguments are required: id' in result.stdout

    def test_invalid_primary_key(self, cli):
        result = cli([
            'awx', 'users', 'modify', '99999999', '--last_name', 'Smith'
        ], auth=True)
        assert result.returncode == 1
        assert result.json['detail'] == 'Not found.'

    def test_valid_update(self, cli, anonymous_user):
        assert anonymous_user.get().last_name != 'Smith'
        result = cli([
            'awx', 'users', 'modify', str(anonymous_user.id),
            '--last_name', 'Smith'
        ], auth=True)
        assert result.returncode == 0
        assert anonymous_user.get().last_name == 'Smith'
