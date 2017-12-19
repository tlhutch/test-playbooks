import json

from towerkit.api.resources import resources
from towerkit.tower import license
import fauxfactory
import pytest

from tests.api.license import LicenseTest


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
class TestEnterpriseLicense(LicenseTest):

    @pytest.fixture
    def basic_license_json(self):
        return license.generate_license(instance_count=self.license_instance_count,
                                        days=31,
                                        company_name=fauxfactory.gen_utf8(),
                                        contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email(),
                                        license_type="basic")

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)

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
        assert conf.license_info['license_type'] == 'enterprise', \
            "Incorrect license_type returned. Expected 'enterprise,' " \
            "returned %s." % conf.license_info['license_type']

        default_features = {u'surveys': True,
                            u'multiple_organizations': True,
                            u'activity_streams': True,
                            u'ldap': True,
                            u'ha': True,
                            u'system_tracking': True,
                            u'enterprise_auth': True,
                            u'rebranding': True,
                            u'workflows': True}

        # assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for enterprise license: %s." % conf.license_info

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/7834')
    def test_job_launch(self, job_template):
        """Verify that job templates can be launched."""
        job_template.launch_job().wait_until_completed()

    def test_post_multiple_organizations(self, api_organizations_pg):
        """Verify that multiple organizations may exist with an enterprise license."""
        # create second organization
        payload = dict(name="org-%s" % fauxfactory.gen_utf8(),
                       description="Random organization - %s" % fauxfactory.gen_utf8())
        api_organizations_pg.post(payload)

        # assert multiple organizations exist
        organizations_pg = api_organizations_pg.get()
        assert organizations_pg.count > 1, "Multiple organizations are supposed" \
            "to exist, but do not. Instead, only %s exist." % api_organizations_pg.count

    def test_create_survey(self, job_template_ping, required_survey_spec):
        """Verify that surveys may be enabled and created with an enterprise license."""
        job_template_ping.add_survey(spec=required_survey_spec)
        survey_spec = job_template_ping.get_related('survey_spec')
        assert survey_spec.spec == required_survey_spec, \
            "Expected /api/v1/job_templates/N/survey_spec/ to reflect our survey_spec."

    def test_activity_stream_get(self, v1):
        """Verify that GET requests to /api/v1/activity_stream/ are allowed with an enterprise license."""
        v1.activity_stream.get()

    def test_able_to_create_workflow_job_template(self, factories):
        factories.v2_workflow_job_template()

    @pytest.mark.fixture_args(older_than='1y', granularity='1y')
    def test_able_to_cleanup_facts(self, cleanup_facts):
        """Verifies that cleanup_facts may be run with an enterprise license."""
        # wait for cleanup_facts to finish
        job_pg = cleanup_facts.wait_until_completed()

        # assert expected failure
        assert job_pg.is_successful, "cleanup_facts job unexpectedly failed " \
            "with an enterprise license - %s" % job_pg

    def test_activity_stream_settings(self, api_settings_system_pg):
        """Verify that activity stream flags are visible with an enterprise license."""
        settings_pg = api_settings_system_pg.get()
        assert all(flag in settings_pg.json for flag in self.ACTIVITY_STREAM_FLAGS), \
            "Activity stream flags not visible under /api/v1/settings/system/ with an enterprise license."

    def test_custom_rebranding_settings(self, api_settings_ui_pg):
        """Verify that custom rebranding flags are visible with an enterprise license."""
        for flag in self.REBRANDING_FLAGS:
            assert flag in api_settings_ui_pg.json, \
                "Flag '{0}' not displayed under /api/v1/settings/ui/ with an enterprise license.".format(flag)

    def test_main_settings_endpoint(self, api_settings_pg):
        """Verify that the top-level /api/v1/settings/ endpoint shows our
        enterprise auth endpoints.
        """
        endpoints = [setting.endpoint for setting in api_settings_pg.results]
        assert(resources.v1_settings_saml in endpoints), \
            "Expected to find an /api/v1/settings/saml/ entry under /api/v1/settings/."
        assert(resources.v1_settings_radius in endpoints), \
            "Expected to find an /api/v1/settings/radius/ entry under /api/v1/settings/."
        assert(resources.v1_settings_ldap in endpoints), \
            "Expected to find an /api/v1/settings/ldap/ entry under /api/v1/settings/."

    def test_nested_enterprise_auth_endpoints(self, api_settings_pg):
        """Verify that enterprise license users have access to our enterprise
        authentication settings pages.
        """
        for service in self.ENTERPRISE_AUTH_SERVICES:
            api_settings_pg.get_endpoint(service)

    def test_downgrade_to_basic(self, basic_license_json, api_config_pg):
        """Verify that an enterprise license can get downgraded to a basic license by posting to api_config_pg."""
        # Update the license
        api_config_pg.post(basic_license_json)

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key

        # Assess license type
        conf = api_config_pg.get()
        assert conf.license_info['license_type'] == 'basic', \
            "Incorrect license_type returned. Expected 'basic,' " \
            "returned %s." % conf.license_info['license_type']

        # Assert license_key is correct
        expected_license_key = basic_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)

    def test_delete_license(self, api_config_pg):
        """Verify the license_info field is empty after deleting the license"""
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info,
                                                                                               indent=2)

    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)


@pytest.mark.api
@pytest.mark.skip_selenium
class TestEnterpriseLicenseExpired(LicenseTest):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_expired')

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)

        # Assert NOT Demo mode
        assert not conf.is_demo_license

        # Assert NOT AWS information
        assert not conf.is_aws_license

        # Assert the license is valid
        assert conf.is_valid_license

        # Assert dates look sane?
        assert conf.license_info.date_expired
        assert conf.license_info.date_warning

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000

        # Assess license type
        assert conf.license_info['license_type'] == 'enterprise', \
            "Incorrect license_type returned. Expected 'enterprise' " \
            "returned %s." % conf.license_info['license_type']

    @pytest.mark.fixture_args(days=1000, older_than='5y', granularity='5y')
    def test_system_job_launch(self, system_job_with_status_completed):
        """Verify that system jobs can be launched"""
        assert system_job_with_status_completed.is_successful, (
            "System job unexpectedly failed - %s" % system_job_with_status_completed)
