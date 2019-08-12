import fauxfactory
import pytest

from awxkit import config

from tests.cli.utils import format_error


@pytest.mark.yolo
class TestDetailView(object):

    def test_404(self, cli):
        result = cli(['awx', 'users', 'get', '10000'], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.json == {'detail': 'Not found.'}

    def test_404_yaml(self, cli):
        result = cli(['awx', 'users', 'get', '10000', '-f', 'yaml'], auth=True)
        assert result.returncode == 1, format_error(result)
        assert result.yaml == {'detail': 'Not found.'}

    def test_404_verbose(self, cli):
        result = cli(['awx', 'users', 'get', '10000', '-v'], auth=True)
        assert result.returncode == 1, format_error(result)
        assert b'"GET /api/v2/users/10000/ HTTP/1.1" 404' in result.stdout

    @pytest.mark.parametrize('resource', ['users', 'organizations'])
    def test_get(self, cli, resource):
        result = cli(['awx', resource, 'get', '1'], auth=True)
        assert result.returncode == 0, format_error(result)
        for col in ('id', 'url', 'created'):
            assert col in result.json.keys()


class TestListView(object):

    @pytest.mark.parametrize('resource', ['users', 'organizations'])
    def test_list_actions(self, cli, resource):
        result = cli(['awx', resource], auth=True)
        assert result.returncode == 2, format_error(result)
        assert bytes(
            'usage: awx {} [-h] action'.format(resource),
            encoding='utf-8'
        )in result.stdout
        for action in (b'list', b'create', b'get', b'modify', b'delete'):
            assert action in result.stdout

    def test_simple_list(self, cli):
        result = cli(['awx', 'users', 'list'], auth=True)
        assert result.json['count'] >= 1

    def test_filtering_match(self, cli):
        me = config.credentials.users.admin.username
        result = cli(['awx', 'users', 'list', '--username', me], auth=True)
        assert result.json['count'] == 1

    def test_filtering_miss(self, cli):
        result = cli(['awx', 'users', 'list', '--username', 'XYZ'], auth=True)
        assert result.json['count'] == 0

    @pytest.mark.usefixtures('authtoken')
    def test_fetch_all_pages(self, cli, v2, api_labels_pg, organization):
        for i in range(80):
            payload = dict(
                name="label %s - %s" % (i, fauxfactory.gen_utf8()),
                organization=organization.id
            )
            api_labels_pg.post(payload)

        result = cli(['awx', 'labels', 'list'], auth=True)
        assert result.json['count'] == 80
        assert len(result.json['results']) == 25

        result = cli(['awx', 'labels', 'list', '--all'], auth=True)
        assert result.json['count'] == 80
        assert len(result.json['results']) == 80
