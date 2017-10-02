import logging
import json

from towerkit.api.resources import resources
import towerkit.exceptions as exc
import fauxfactory
import pytest

from tests.api.license import LicenseTest


log = logging.getLogger(__name__)


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_legacy_license')
class TestLegacyLicense(LicenseTest):

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
        assert conf.license_info['license_type'] == 'legacy', \
            "Incorrect license_type returned. Expected 'legacy,' " \
            "returned %s." % conf.license_info['license_type']

        default_features = {u'surveys': True,
                            u'multiple_organizations': True,
                            u'activity_streams': True,
                            u'ldap': True,
                            u'ha': True,
                            u'system_tracking': False,
                            u'enterprise_auth': False,
                            u'rebranding': False,
                            u'workflows': False}

        # Assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for legacy license: %s." % conf.license_info

    def test_duplicate_hosts_counted_once(self, factories, v2):
        config = v2.config.get()
        current_instances = config.license_info.current_instances

        for _ in range(2):
            factories.v2_host(name="host")
        assert config.get().license_info.current_instances == current_instances + 1

    def test_job_launch(self, job_template):
        """Verify that job templates can be launched."""
        job_template.launch_job().wait_until_completed()

    def test_post_multiple_organizations(self, factories):
        """Verify that multiple organizations may exist with a legacy license."""
        for _ in range(2):
            factories.organization()

    def test_create_survey(self, job_template_ping, required_survey_spec):
        """Verify that surveys may be enabled and created with a legacy license."""
        job_template_ping.add_survey(spec=required_survey_spec)
        assert job_template_ping.get_related('survey_spec').spec == required_survey_spec, \
            "Expected /api/v1/job_templates/N/survey_spec/ to reflect our survey_spec."

    def test_unable_to_create_workflow_job_template(self, factories, default_organization):
        with pytest.raises(exc.PaymentRequired) as e:
            factories.v2_workflow_job_template(organization=default_organization)
        assert e.value[1]['detail'] == 'Your license does not allow use of workflows.'

    def test_activity_stream_get(self, v1):
        """Verify that GET requests to /api/v1/activity_stream/ are allowed with a legacy license."""
        v1.activity_stream.get()

    @pytest.mark.fixture_args(older_than='1y', granularity='1y')
    def test_unable_to_cleanup_facts(self, cleanup_facts):
        """Verify that cleanup_facts may not be run with a legacy license."""
        # wait for cleanup_facts to finish
        job_pg = cleanup_facts.wait_until_completed()

        # assert expected failure
        assert job_pg.status == 'failed', "cleanup_facts job " \
            "unexpectedly passed with a legacy license - %s" % job_pg

        # assert expected stdout
        assert job_pg.result_stdout == "CommandError: The System Tracking " \
            "feature is not enabled for your instance\r\n", \
            "Unexpected stdout when running cleanup_facts with a legacy license."

    def test_unable_to_get_fact_versions(self, host_local):
        """Verify that GET requests are rejected from fact_versions."""
        exc_info = pytest.raises(exc.PaymentRequired, host_local.get_related, 'fact_versions')
        result = exc_info.value[1]

        assert result == {u'detail': u'Your license does not permit use of system tracking.'}, (
            "Unexpected API response upon attempting to navigate to fact_versions with a legacy license - %s."
            % json.dumps(result))

    def test_activity_stream_settings(self, api_settings_system_pg):
        """Verify that activity stream flags are visible with a legacy license."""
        assert all(flag in api_settings_system_pg.json for flag in self.ACTIVITY_STREAM_FLAGS), \
            "Activity stream flags not visible under /api/v1/settings/system/ with a legacy license."

    def test_custom_rebranding_settings(self, api_settings_ui_pg):
        """Verify that custom rebranding flags are not visible with a legacy license."""
        for flag in api_settings_ui_pg.json.keys():
            assert flag not in self.REBRANDING_FLAGS, \
                "Flag '{0}' visible under /api/v1/settings/ui/ with a legacy license.".format(flag)

    def test_main_settings_endpoint(self, api_settings_pg):
        """Verify that the top-level /api/v1/settings/ endpoint shows only
        LDAP among our enterprise auth solutions. Note: LDAP is a special
        case with legacy licenses.
        """
        endpoints = [setting.endpoint for setting in api_settings_pg.results]
        assert(resources.v1_settings_saml not in endpoints), \
            "Expected not to find an /api/v1/settings/saml/ entry under /api/v1/settings/."
        assert(resources.v1_settings_radius not in endpoints), \
            "Expected not to find an /api/v1/settings/radius/ entry under /api/v1/settings/."
        assert(resources.v1_settings_ldap in endpoints), \
            "Expected to find an /api/v1/settings/ldap/ entry under /api/v1/settings/."

    def test_nested_enterprise_auth_endpoints(self, api_settings_pg):
        """Verify that legacy license users have access to LDAP only from our
        enterprise authentication settings pages.
        """
        for service in self.ENTERPRISE_AUTH_SERVICES:
            if service == 'ldap':
                api_settings_pg.get_endpoint(service)
            else:
                with pytest.raises(exc.NotFound):
                    api_settings_pg.get_endpoint(service)

    def test_upgrade_to_enterprise(self, enterprise_license_json, api_config_pg):
        """Verify that a legacy license can get upgraded to an enterprise license."""
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

    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)


@pytest.mark.api
@pytest.mark.skip_selenium
class TestLegacyLicenseWarning(LicenseTest):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_legacy_license_warning')

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
        assert not conf.license_info.date_expired
        assert conf.license_info.date_warning

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000

        # Assess license type
        assert conf.license_info['license_type'] == 'legacy', \
            "Incorrect license_type returned. Expected 'legacy,' " \
            "returned %s." % conf.license_info['license_type']

    def test_update_license(self, api_config_pg, legacy_license_json):
        """Verify that the license can be updated by issuing a POST to the /config endpoint"""
        # Record license_key
        conf = api_config_pg.get()
        before_license_key = conf.license_info.license_key

        # Update the license
        api_config_pg.post(legacy_license_json)

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key
        assert before_license_key != after_license_key, \
            "Expected license_key to change after applying new license, but found old value."

        # Assert license_key is correct
        expected_license_key = legacy_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)

    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)


@pytest.mark.api
@pytest.mark.skip_selenium
class TestLegacyLicenseGracePeriod(LicenseTest):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_legacy_license_grace_period')

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
        assert conf.license_info['license_type'] == 'legacy', \
            "Incorrect license_type returned. Expected 'legacy,' " \
            "returned %s." % conf.license_info['license_type']

    def test_job_launch(self, api_config_pg, job_template):
        """Verify that job_templates can be launched while there are remaining free_instances"""
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")
        else:
            job_template.launch_job().wait_until_completed()

    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)


@pytest.mark.api
@pytest.mark.skip_selenium
class TestLegacyLicenseExpired(LicenseTest):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_legacy_license_expired')

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
        assert conf.license_info['license_type'] == 'legacy', \
            "Incorrect license_type returned. Expected 'legacy,' " \
            "returned %s." % conf.license_info['license_type']

    def test_cannot_add_host(self, api_hosts_pg, inventory, group):
        """Verify that no hosts can be added"""
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       description="host-%s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        with pytest.raises(exc.LicenseExceeded):
            inventory.related.hosts.post(payload)
        with pytest.raises(exc.LicenseExceeded):
            group.related.hosts.post(payload)
        with pytest.raises(exc.LicenseExceeded):
            api_hosts_pg.post(payload)

    def test_job_launch(self, request, factories, apply_generated_license):
        """Verify that job_templates cannot be launched"""
        with apply_generated_license(self.legacy_license_json()):
            job_template = factories.v2_job_template()

        with pytest.raises(exc.LicenseExceeded):
            job_template.launch_job()

    @pytest.mark.fixture_args(days=1000, older_than='5y', granularity='5y')
    def test_system_job_launch(self, system_job):
        """Verify that system jobs can be launched"""
        # launch job and assess success
        system_job.wait_until_completed()

        # cleanup_facts jobs will fail if the license does not support it
        if system_job.job_type == 'cleanup_facts':
            assert system_job.status == 'failed', "System job unexpectedly succeeded - %s" % system_job
            assert system_job.result_stdout == ("CommandError: The System Tracking feature is not enabled for "
                                                "your instance\r\n")
        # all other system_jobs are expected to succeed
        else:
            assert system_job.is_successful, "System job unexpectedly failed - %s" % system_job

    def test_unable_to_launch_ad_hoc_command(self, request, apply_generated_license, api_ad_hoc_commands_pg,
                                             ssh_credential):
        """Verify that ad hoc commands cannot be launched from all four ad hoc endpoints."""
        with apply_generated_license(self.legacy_license_json()):
            host_local = request.getfixturevalue('host_local')

        ad_hoc_commands_pg = api_ad_hoc_commands_pg.get()
        inventory_pg = host_local.get_related('inventory')
        group_pg = host_local.get_related('groups').results[0]

        # create payload
        payload = dict(job_type="run",
                       inventory=inventory_pg.id,
                       credential=ssh_credential.id,
                       module_name="ping")

        for endpoint in [inventory_pg, group_pg, host_local]:
            ad_hoc_commands_pg = endpoint.get_related('ad_hoc_commands')
            with pytest.raises(exc.LicenseExceeded):
                ad_hoc_commands_pg.post(payload), ("Unexpectedly launched an ad_hoc_command with an expired "
                                                   "license from %s." % ad_hoc_commands_pg.endpoint)

    def test_update_license(self, api_config_pg, legacy_license_json):
        """Verify that the license can be updated by issuing a POST to the /config endpoint"""
        # Record license_key
        conf = api_config_pg.get()
        before_license_key = conf.license_info.license_key

        # Update the license
        api_config_pg.post(legacy_license_json)

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key
        assert before_license_key != after_license_key, \
            "Expected license_key to change after applying new license, but found old value."

        # Assert license_key is correct
        expected_license_key = legacy_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)


@pytest.mark.api
@pytest.mark.skip_selenium
class TestLegacyTrialLicense(LicenseTest):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_trial_legacy_license')

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)

        # Assert NOT Demo mode
        assert not conf.is_demo_license

        # Assert a valid key
        assert conf.is_trial_license

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert not conf.license_info.date_warning

        # Assert not AWS information
        assert not conf.is_aws_license

        # Assert there is no grace_period, it should match time_remaining
        assert conf.license_info['grace_period_remaining'] == conf.license_info['time_remaining']

        # Assess license type
        assert conf.license_info['license_type'] == 'legacy', \
            "Incorrect license_type returned. Expected 'legacy,' " \
            "returned %s." % conf.license_info['license_type']

    def test_key_visibility_superuser(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert conf.is_trial_license

    def test_key_visibility_non_superuser(self, api_config_pg, non_superuser, user_password):
        with self.current_user(non_superuser.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)

            if non_superuser.is_system_auditor:
                assert 'license_key' in conf.license_info
            else:
                assert 'license_key' not in conf.license_info

    def test_update_license(self, api_config_pg, trial_legacy_license_json):
        """Verify that the license can be updated by issuing a POST to the /config endpoint"""
        # Record license_key
        conf = api_config_pg.get()
        before_license_key = conf.license_info.license_key

        # Update the license
        api_config_pg.post(trial_legacy_license_json)

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key
        assert before_license_key != after_license_key, \
            "Expected license_key to change after applying new license, but found old value."

        # Assert license_key is correct
        expected_license_key = trial_legacy_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)

    def test_instance_counts(self, request, api_config_pg, api_hosts_pg, inventory, group):
        self.assert_instance_counts(request, api_config_pg, api_hosts_pg, group)
