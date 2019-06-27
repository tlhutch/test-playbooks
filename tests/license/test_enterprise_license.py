import json

from towerkit.api.resources import resources
from towerkit.tower import license
import fauxfactory
import pytest

from tests.license.license import LicenseTest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license')
class TestEnterpriseLicense(LicenseTest):

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
        assert conf.license_info['license_type'] == 'enterprise', \
            "Incorrect license_type returned. Expected 'enterprise,' " \
            "returned %s." % conf.license_info['license_type']

        default_features = {'surveys': True,
                            'multiple_organizations': True,
                            'activity_streams': True,
                            'ldap': True,
                            'ha': True,
                            'system_tracking': True,
                            'enterprise_auth': True,
                            'rebranding': True,
                            'workflows': True}

        # assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for enterprise license: %s." % conf.license_info

    def test_job_launch(self, job_template):
        """Verify that job templates can be launched."""
        job_template.launch().wait_until_completed()

    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)

    @pytest.fixture
    def basic_license_json(self):
        return license.generate_license(instance_count=self.license_instance_count,
                                        days=31,
                                        company_name=fauxfactory.gen_utf8(),
                                        contact_name=fauxfactory.gen_utf8(),
                                        contact_email=fauxfactory.gen_email(),
                                        license_type="basic")

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


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_expired')
class TestEnterpriseLicenseExpired(LicenseTest):

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print(json.dumps(conf.json, indent=4))

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
        system_job_with_status_completed.assert_successful()
