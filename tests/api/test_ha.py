import pytest
import httplib
import requests
from tests.api import Base_Api_Test


def assert_instance_role(url, role='primary'):
    result = requests.get(url, verify=False)
    assert result.status_code == httplib.OK

    # assert that http traffic was *NOT* redirected
    assert len(result.history) == 0, "No http redirects were expected"
    json = result.json()

    # assert various JSON response attributes
    assert json['ha']
    assert json['role'] == role, \
        "Instance reports unexpected role (%s != %s)" % \
        (role, json['role'])
    return json


@pytest.fixture(scope="function")
def ensure_primary(request, ansible_module):
    """Ensures the the HA primary is restored on teardown."""
    def teardown():
        contacted = ansible_module.command('awx-manage update_instance --primary')
        for result in contacted.values():
            assert result['rc'] == 0, "Unexpected return code (%s != 0)" % result['rc']
            assert result['stdout'].startswith("Successfully updated instance role")
    request.addfinalizer(teardown)


@pytest.mark.api
@pytest.mark.requires_ha
@pytest.mark.skip_selenium
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_HA(Base_Api_Test):

    @pytest.mark.ansible(host_pattern='primary')
    def test_primary_ping_endpoint(self, api_ping_pg, ansible_module):
        """Verify /api/v1/ping on the HA primary"""
        api_ping_pg.get()
        assert api_ping_pg.ha
        assert api_ping_pg.role == 'primary'

    @pytest.mark.ansible(host_pattern='primary')
    def test_secondary_ping_endpoint(self, api_ping_pg, api_ping_url, ansible_module):
        """Verify /api/v1/ping on the HA primary"""
        api_ping_pg.get()
        secondaries = api_ping_pg.instances['secondaries']
        assert len(secondaries) > 0, "Unexpected number of HA secondary instances (%s)" % len(secondaries)

        for secondary in secondaries:
            json = assert_instance_role("https://" + secondary + api_ping_url, role='secondary')
            # assert expected number of secondaries
            assert len(json['instances']['secondaries']) == len(api_ping_pg.instances['secondaries'])

    @pytest.mark.ansible(host_pattern='primary')
    def test_secondary_endpoint_redirect(self, api_ping_pg, api_v1_url, ansible_module):
        """Verify secondary endpoints redirect to the primary."""
        api_ping_pg.get()
        primary = api_ping_pg.instances['primary']
        secondaries = api_ping_pg.instances['secondaries']
        assert len(secondaries) > 0, "Unexpected number of HA secondary instances (%s)" % len(secondaries)
        assert primary not in secondaries

        # Assert that each secondary redirects traffic to the primary
        for secondary in secondaries:
            result = requests.get("https://" + secondary + api_v1_url, verify=False)
            assert result.status_code == httplib.OK

            # assert that HTTP traffic *was* redirected
            assert len(result.history) == 1, "HTTP redirects where expected"
            assert result.history[0].status_code == httplib.FOUND
            assert primary in result.history[0].headers['location']

    @pytest.mark.ansible(host_pattern='primary')
    def test_list_instances(self, ansible_module, api_ping_pg):
        """Verifies that 'awx-manage list_instances' returns expected results"""
        expected_instances = len(api_ping_pg.get().instances['secondaries']) + 1

        contacted = ansible_module.command('awx-manage list_instances')
        for result in contacted.values():
            assert result['rc'] == 0, "Unexpected return code (%s != %s)" % (result['rc'], 0)

            num_instances = len(result['stdout'].split('\n'))
            assert num_instances == expected_instances, \
                "unexpected number of instances returned by list_instances (%s != %s)" %  \
                (expected_instances, num_instances)

    @pytest.mark.ansible(host_pattern='primary')
    def test_promote_secondary_instances(self, ansible_runner, api_ping_url, api_ping_pg, ensure_primary):
        """Verify that 'awx-manage update_instance' can promote all configured
        secondary instances to a primary.  The primary instance is restored
        upon test completion.
        """
        contacted = ansible_runner.command('awx-manage update_instance --primary')
        for result in contacted.values():
            assert result['rc'] == 0, "Unexpected return code (%s != 0)" % result['rc']
            assert result['stdout'].startswith("Successfully updated instance role")

        api_ping_pg.get()
        # primary = api_ping_pg.instances['primary']
        secondaries = api_ping_pg.instances['secondaries']
        assert len(secondaries) > 0, "Unexpected number of HA secondary instances (%s)" % len(secondaries)

        # promote each secondary
        for secondary in secondaries:
            # assert instance is a secondary
            assert_instance_role("https://" + secondary + api_ping_url, role='secondary')

            # assert successful promotion
            contacted = ansible_runner.command('awx-manage update_instance --hostname %s --primary' % secondary)
            for result in contacted.values():
                assert result['rc'] == 0, "Unexpected return code (%s != 0)" % result['rc']
                assert result['stdout'].startswith("Successfully updated instance role")

            # assert instance is now a primary
            assert_instance_role("https://" + secondary + api_ping_url, role='primary')

    @pytest.mark.ansible(host_pattern='primary')
    def test_cannot_remove_primary_instance(self, ansible_module, api_ping_pg):
        """Verify that 'awx-manage remove_instance' cannot remove the current primary instance."""
        api_ping_pg.get()
        primary = api_ping_pg.instances['primary']

        # assert failure when attempting to remove primary
        contacted = ansible_module.command("awx-manage remove_instance --hostname %s" % primary)
        for result in contacted.values():
            assert result['rc'] == 1, "Unexpected return code (%s != 1)" % result['rc']
            assert result['stderr'].startswith("CommandError: Cannot remove primary instance")
            assert result['stderr'].endswith("Another instance must be promoted to primary first.")

    @pytest.mark.ansible(host_pattern='primary')
    def test_remove_and_register_instances(self, ansible_module, api_ping_pg):
        """Verifies the 'awx-manage remove_instance' command.  Caution, this
        test will remove all secondary instances from the HA configuration.
        """
        api_ping_pg.get()
        secondaries = api_ping_pg.instances['secondaries']
        num_secondaries = len(secondaries)
        assert num_secondaries > 0, "Unexpected number of HA secondary instances (%s)" % num_secondaries

        # remove and register each secondary
        for count, secondary in enumerate(secondaries, 1):
            # assert successful removal
            contacted = ansible_module.command('awx-manage remove_instance --hostname %s' % secondary)
            for result in contacted.values():
                assert result['rc'] == 0, "Unexpected return code (%s != 0)" % result['rc']
                assert result['stdout'].startswith("Successfully removed instance")

            # assert /api/v1/ping secondary count was decremented
            api_ping_pg.get()
            num_secondaries -= 1
            secondaries = api_ping_pg.instances['secondaries']
            assert len(secondaries) == num_secondaries, \
                "Unexpected number of HA secondary instances (%s != %s)" % \
                (num_secondaries, len(secondaries))

            # assert successful registration (TODO needs to be done *on* the
            # secondary itself)
