import json

import pytest

from tests.license.license import LicenseTest


@pytest.mark.serial
@pytest.mark.usefixtures('authtoken', 'install_basic_license')
class TestBasicLicense(LicenseTest):

    def test_basic_license_metadata(self, api_config_pg):
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

        # In 3.5 we no longer limit features based on basic license https://github.com/ansible/tower/issues/3366
        # BUT.....because this becomes part of license hash, we cannot change these values or it breaks people's allready
        # issued basic licenses: https://github.com/ansible/tower-license/pull/8
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

    def test_basic_license_job_launch(self, v2, factories):
        """Verify that job templates can be launched."""
        if v2.hosts.get(page_size=50).count >= 10:
            pytest.skip("Skipping because tower has too many hosts for this to work. Clean up tower and try again.")
        job_template = factories.job_template()
        job_template.launch().wait_until_completed()

    def test_basic_license_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)

    def test_basic_license_upgrade_to_enterprise(self, enterprise_license_json, api_config_pg):
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

    def test_basic_license_delete_license(self, api_config_pg):
        """Verify the license_info field is empty after deleting the license"""
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info,
                                                                                               indent=2)
