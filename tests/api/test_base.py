import httplib

from towerkit.api.schema import validate
import fauxfactory
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.nondestructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Api_Basics(Base_Api_Test):

    def test_get_200(self, connection):
        r = connection.get('/api/')
        assert r.status_code == httplib.OK, "Unable to connect"

    def test_get_404(self, connection):
        r = connection.get('/api/%s/' % fauxfactory.gen_utf8())
        assert r.status_code == httplib.NOT_FOUND

    def test_get_schema(self, connection):
        r = connection.get('/api/')
        assert r.status_code == httplib.OK
        validate(r.json(), '/api/', 'get')

    def test_options_schema(self, connection):
        r = connection.options('/api/')
        assert r.status_code == httplib.OK
        validate(r.json(), '/api/', 'options')

    def test_head_empty(self, connection):
        r = connection.head('/api/')
        assert r.text == '', 'Expected no output from HEAD request'
        assert r.status_code == httplib.OK

    def test_post_fail(self, connection):
        r = connection.post('/api/', {})
        assert r.status_code == httplib.METHOD_NOT_ALLOWED

    def test_patch_fail(self, connection):
        r = connection.patch('/api/', {})
        assert r.status_code == httplib.METHOD_NOT_ALLOWED

    def test_current_version(self, connection):
        r = connection.get('/api/')
        data = r.json()
        current_version = data.get('current_version')
        available_versions = data.get('available_versions')
        assert current_version in available_versions.values(), \
            "Unable to find current_version (%s) in list of " \
            "available_versions (%s)" % \
            (current_version, available_versions.values())

        # Does current_version path work?
        r = connection.get(current_version)
        assert r.status_code == httplib.OK, 'Unexpected response code'
        assert isinstance(r.json(), dict), 'Unexpected response data'

    def test_description(self, connection):
        r = connection.get('/api/')
        data = r.json()
        description = data.get('description')
        assert description == 'AWX REST API'


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestResourceBasics(Base_Api_Test):

    @pytest.mark.parametrize('resource', ['credential_type', 'v2_credential', 'v2_group',
                                          'v2_host', 'v2_inventory', 'v2_inventory_script',
                                          'v2_inventory_source', 'v2_job_template', 'v2_label',
                                          'v2_notification_template', 'v2_organization',
                                          'v2_project', 'v2_team', 'v2_user',
                                          'v2_workflow_job_template', 'v2_workflow_job_template_node'])
    def test_all_resources_can_have_name_and_descriptions_changed(self, factories, resource):
        instance = getattr(factories, resource)()
        instance.name = "TestName"
        instance.description = "TestDescription"
        assert instance.get().name == "TestName"
        assert instance.description == "TestDescription"
