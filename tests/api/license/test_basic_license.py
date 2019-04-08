import json

from towerkit.api.resources import resources
import towerkit.exceptions as exc
import pytest

from tests.api.license import LicenseTest


@pytest.mark.api
@pytest.mark.mp_group(group="TestBasicLicense", strategy="isolated_free")
@pytest.mark.usefixtures('authtoken', 'install_basic_license')
class TestBasicLicense(LicenseTest):

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print(json.dumps(conf.json, indent=4))

        # Assert NOT Demo mode
        assert not conf.is_demo_license

        # Assert NOT AWS
        assert not conf.is_aws_license

        # Assert the license is valid
        assert conf.is_valid_license

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert not conf.license_info.date_warning

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000

        # Assess license type
        assert conf.license_info['license_type'] == 'basic', \
            "Incorrect license_type returned. Expected 'basic,' " \
            "returned %s." % conf.license_info['license_type']

        default_features = {'surveys': False,
                            'multiple_organizations': False,
                            'activity_streams': False,
                            'ldap': False,
                            'ha': False,
                            'system_tracking': False,
                            'enterprise_auth': False,
                            'rebranding': False,
                            'workflows': False}

        # assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for basic license: %s." % conf.license_info

    def test_job_launch(self, job_template):
        """Verify that job templates can be launched."""
        job_template.launch().wait_until_completed()

    def test_unable_to_create_multiple_organizations(self, factories, api_organizations_pg):
        """Verify that attempting to create a second organization with a basic license raises a 402."""
        # verify that we have a prestocked organization
        assert api_organizations_pg.get(name="Default").count == 1, \
            "Default organization not found."
        # attempting to create an additional organization should trigger a 402
        with pytest.raises(exc.PaymentRequired):
            factories.organization()

    def test_unable_to_create_survey(self, job_template_ping, required_survey_spec):
        """Verify that attempting to enable and create a survey with a basic license raises a 402."""
        with pytest.raises(exc.PaymentRequired) as e:
            job_template_ping.survey_enabled = True

        assert e.value[1] == {'detail': 'Feature surveys is not enabled in the active license.'}

        with pytest.raises(exc.PaymentRequired) as e:
            job_template_ping.related.survey_spec.post(dict(spec=required_survey_spec))

        assert e.value[1] == {'detail': 'Your license does not allow adding surveys.'}

    def test_unable_to_create_workflow_job_template(self, factories, default_organization):
        with pytest.raises(exc.PaymentRequired) as e:
            factories.v2_workflow_job_template(organization=default_organization)
        assert e.value[1]['detail'] == 'Your license does not allow use of workflows.'

    def test_activity_stream_get(self, v1):
        """Verify that GET requests to /api/v1/activity_stream/ raise 402s."""
        exc_info = pytest.raises(exc.PaymentRequired, v1.activity_stream.get)
        result = exc_info.value[1]
        result == {'detail': 'Your license does not allow use of the activity stream.'}, (
            "Unexpected API response when issuing a GET to /api/v1/activity_stream/ with a basic license - %s."
            % json.dumps(result))

    def test_unable_to_get_fact_versions(self, host_local):
        """Verify that GET requests are rejected from fact_versions."""
        exc_info = pytest.raises(exc.PaymentRequired, host_local.get_related, 'fact_versions')
        result = exc_info.value[1]

        assert result == {'detail': 'Your license does not permit use of system tracking.'}, (
            "Unexpected JSON response upon attempting to navigate to fact_versions with a basic license - %s."
            % json.dumps(result))

    def test_activity_stream_settings(self, api_settings_system_pg):
        """Verify that activity stream flags are not visible with a basic license."""
        assert not any([flag in api_settings_system_pg.json for flag in self.ACTIVITY_STREAM_FLAGS]), \
            "Activity stream flags not visible under /api/v1/settings/system/ with a basic license."

    def test_custom_rebranding_settings(self, api_settings_ui_pg):
        """Verify that custom rebranding flags are not accessible with a basic license."""
        for flag in api_settings_ui_pg.json:
            assert flag not in self.REBRANDING_FLAGS, \
                "Flag '{0}' visible under /api/v1/settings/ui/ with a basic license.".format(flag)

    def test_main_settings_endpoint(self, api_settings_pg):
        """Verify that the top-level /api/v1/settings/ endpoint does not show
        our enterprise auth endpoints.
        """
        endpoints = [setting.endpoint for setting in api_settings_pg.results]
        assert(resources.v1_settings_saml not in endpoints), \
            "Expected not to find an /api/v1/settings/saml/ entry under /api/v1/settings/."
        assert(resources.v1_settings_radius not in endpoints), \
            "Expected not to find an /api/v1/settings/radius/ entry under /api/v1/settings/."
        assert(resources.v1_settings_ldap not in endpoints), \
            "Expected not to find an /api/v1/settings/ldap/ entry under /api/v1/settings/."

    def test_nested_enterprise_auth_endpoints(self, api_settings_pg):
        """Verify that basic license users do not have access to any of our enterprise
        authentication settings pages.
        """
        for service in self.ENTERPRISE_AUTH_SERVICES:
            with pytest.raises(exc.NotFound):
                api_settings_pg.get_endpoint(service)

    def test_job_template_cannot_be_sliced_with_basic_license(self, v2, factories):
        default_org = v2.organizations.get(id=1).results.pop()
        inventory = factories.v2_inventory(organization=default_org)
        project = factories.v2_project(organization=default_org)
        credential = factories.v2_credential(organization=default_org)
        jt = factories.v2_job_template(organization=default_org,
                                       inventory=inventory,
                                       project=project,
                                       credential=credential)
        with pytest.raises(exc.PaymentRequired) as e:
            jt.job_slice_count = 2
        assert e.value.msg == {'job_slice_count': ['Job slicing is a workflows-based feature and your license does not allow use of workflows.']}


@pytest.mark.api
@pytest.mark.mp_group(group="TestBasicLicenseSerial", strategy="isolated_serial")
@pytest.mark.usefixtures('authtoken', 'install_basic_license')
class TestBasicLicenseSerial(LicenseTest):

    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)

    def test_upgrade_to_enterprise(self, enterprise_license_json, api_config_pg):
        """Verify that a basic license can get upgraded to an enterprise license."""
        # Update the license
        api_config_pg.post(enterprise_license_json)

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key

        # Assert license_key is correct
        expected_license_key = enterprise_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)

        # Confirm enterprise license present
        conf = api_config_pg.get()
        assert conf.license_info['license_type'] == 'enterprise', \
            "Incorrect license_type returned. Expected 'enterprise,' " \
            "returned %s." % conf.license_info['license_type']

    def test_delete_license(self, api_config_pg):
        """Verify the license_info field is empty after deleting the license"""
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info,
                                                                                               indent=2)
