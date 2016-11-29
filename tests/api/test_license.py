'''
# Test No License
[X] Test that config.license_info is empty before license is added
[X] Test that you cannot add hosts without a license
[X] Test can launch project updates
[X] Test inventory updates launch but fail
[X] Test can't launch job without license
[X] Tests that invalid licenses get rejected
[X] Test that if you post a legacy licenses with no EULA that the post gets rejected
[X] Tests that if you post a legacy licenses and reject the EULA that the post gets rejected
[X] Tests that you can post a legacy license

# Test Legacy License
[X] Test metadata
[X] Verify that hosts can be added to license maximum
[X] Verify that license_key is visible to admin user
[X] Verify that license_key is not visible to non-admin users
[X] Test cannot create scan job templates
[] Test cannot run scan jobs
[X] Test cannot run cleanup_facts
[X] Test cannot GET fact_versions endpoints
[X] Test can delete license

# Test Legacy License Warning
[X] Test metadata
[X] Test that you can update the license by posting a new one

# Test Legacy License Grace Period
[X] Test metadata
[X] Test that hosts can be added to license maximum
[X] Test that jobs can be launched if there are remaining free instances

# Test Legacy License Expired
[X] Test metadata
[X] Tests that no hosts can be added
[X] Test that job templates cannot be launched
[X] Test that system jobs can be launched
[X] Test that ad hoc commands cannot be launched from all four endpoints
[X] Test that you can post a new license to the api/v1/config endpoint

# Test Legacy Trial License
[X] Test metadata
[X] Test that you can add hosts up to limit
[X] Test that admins can see the product key
[X] Test that non-admins cannot see the product key
[X] Test that you can update the license by posting to api/v1/config

# Test Basic License
[X] Test metadata
[X] Test can add hosts to limit
[X] Test admin can see license key
[X] Test non-admin cannot see license key
[X] Test can launch jobs
[X] Test cannot post multiple organizations
[X] Test cannot create surveys
[X] Test cannot get activity streams
[] Test cannot promote secondary
[] Test that LDAP is disabled
[X] Test cannot create scan JT
[] Test cannot run scan jobs
[X] Test cannot launch cleanup_facts
[X] Test cannot GET fact_versions endpoints
[X] Test upgrade to enterprise
[X] Test can delete license

# Test Enterprise License
[X] Test metadata
[X] Test can add hosts to limit
[X] Test admin can see key
[X] Test non-admins cannot see keys
[X] Test can launch job
[X] Test can post multiple organizations
[X] Test can create surveys
[X] Test can get activity streams
[] Test can promote secondary
[] Test that LDAP is enabled
[X] Test can create scan JT
[X] Test can launch scan jobs
[X] Test can launch cleanup_facts
[X] Test can GET fact_versions endpoints
[X] Test downgrade to basic
[X] Test able to delete license

# Test Enterprise Expired
[X] Test metadata
[X] Can launch system jobs
'''

import json
import logging

import towerkit.tower.license
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope='class')
def license_instance_count(request):
    '''Number of host instances permitted by the license'''
    return 10


@pytest.fixture(scope='function')
def legacy_license_json(request, license_instance_count):
    return towerkit.tower.license.generate_license(instance_count=license_instance_count,
                                                   days=31,
                                                   company_name=fauxfactory.gen_utf8(),
                                                   contact_name=fauxfactory.gen_utf8(),
                                                   contact_email=fauxfactory.gen_email())


@pytest.fixture(scope='function')
def basic_license_json(request, license_instance_count):
    return towerkit.tower.license.generate_license(instance_count=license_instance_count,
                                                   days=31,
                                                   company_name=fauxfactory.gen_utf8(),
                                                   contact_name=fauxfactory.gen_utf8(),
                                                   contact_email=fauxfactory.gen_email(),
                                                   license_type="basic")


@pytest.fixture(scope='function')
def enterprise_license_json(request, license_instance_count):
    return towerkit.tower.license.generate_license(instance_count=license_instance_count,
                                                   days=31,
                                                   company_name=fauxfactory.gen_utf8(),
                                                   contact_name=fauxfactory.gen_utf8(),
                                                   contact_email=fauxfactory.gen_email(),
                                                   license_type="enterprise")


@pytest.fixture(
    scope="function",
    params=[None, 0, 1, -1, True, fauxfactory.gen_utf8(), (), {}, {'eula_accepted': True}],
)
def invalid_license_json(request):
    return request.param


@pytest.fixture(scope='function')
def missing_eula_legacy_license_json(request, legacy_license_json):
    del legacy_license_json['eula_accepted']
    return legacy_license_json


@pytest.fixture(scope='function')
def eula_rejected_legacy_license_json(request, legacy_license_json):
    legacy_license_json['eula_accepted'] = False
    return legacy_license_json


@pytest.fixture(scope='function')
def trial_legacy_license_json(request, license_instance_count):
    return towerkit.tower.license.generate_license(instance_count=license_instance_count,
                                                   days=31,
                                                   trial=True,
                                                   company_name=fauxfactory.gen_utf8(),
                                                   contact_name=fauxfactory.gen_utf8(),
                                                   contact_email=fauxfactory.gen_email())


@pytest.fixture(scope='function')
def install_trial_legacy_license(request, api_config_pg, license_instance_count):
    log.debug("calling fixture install_trial_legacy_license")
    license_info = towerkit.tower.license.generate_license(instance_count=license_instance_count, days=31, trial=True)
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)

    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Expected valid license, invalid license found'

    # Confirm license type, license_key have expected values
    assert conf.is_legacy_license, \
        "Expected legacy license, found %s." % conf.license_info.license_type
    assert conf.is_trial_license, \
        "Expected trial license, found regular license"
    assert conf.license_info.license_key == license_info['license_key'], \
        "License found differs from license applied"


@pytest.fixture(scope='function')
def install_legacy_license(request, api_config_pg, legacy_license_json):
    # Apply license
    log.debug("calling fixture install_legacy_license")
    api_config_pg.post(legacy_license_json)
    request.addfinalizer(api_config_pg.delete)

    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Expected valid license, invalid license found'

    # Confirm license type, license_key have expected values
    assert conf.is_legacy_license, \
        "Expected legacy license, found %s." % conf.license_info.license_type
    assert conf.license_info.license_key == legacy_license_json['license_key'], \
        "License found differs from license applied"


@pytest.fixture(scope='function')
def install_basic_license(request, api_config_pg, license_instance_count):
    log.debug("calling fixture install_basic_license")
    license_info = towerkit.tower.license.generate_license(instance_count=license_instance_count, days=31, license_type="basic")
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)

    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Expected valid license, invalid license found'

    # Confirm license type, license_key have expected values
    assert conf.is_basic_license, \
        "Expected basic license, found %s." % conf.license_info.license_type
    assert conf.license_info.license_key == license_info['license_key'], \
        "License found differs from license applied"


@pytest.fixture(scope='function')
def install_enterprise_license(request, ansible_runner, api_config_pg, enterprise_license_json):
    log.debug("calling license fixture install_enterprise_license")

    # POST a license
    api_config_pg.post(enterprise_license_json)

    # Confirm that license is present
    conf = api_config_pg.get()
    assert conf.is_valid_license, 'Expected valid license, invalid license found'

    # Confirm license type, license_key have expected values
    assert conf.is_enterprise_license, \
        "Expected enterprise license, %s." % conf.license_info.license_type
    assert conf.license_info.license_key == enterprise_license_json['license_key'], \
        "License found differs from license applied"

    def teardown():
        log.debug("calling license teardown install_enterprise_license")

        # Delete the license
        api_config_pg.delete()

        # Pause to allow tower to do it's thing
        ansible_runner.pause(seconds=15)

    request.addfinalizer(teardown)


@pytest.fixture(scope='function')
def install_enterprise_license_expired(request, ansible_runner, api_config_pg, license_instance_count):
    log.debug("calling fixture install_enterprise_license_expired")

    license_info = towerkit.tower.license.generate_license(license_type='enterprise', instance_count=license_instance_count, days=-61)
    api_config_pg.post(license_info)

    def teardown():
        log.debug("calling license teardown install_enterprise_license_expired")
        # Delete the license
        api_config_pg.delete()

        # Pause to allow tower to do it's thing
        ansible_runner.pause(seconds=15)

    request.addfinalizer(teardown)


@pytest.fixture(scope='function')
def install_legacy_license_warning(request, api_config_pg, license_instance_count):
    log.debug("calling fixture install_legacy_license_warning")

    # Post license
    license_info = towerkit.tower.license.generate_license(instance_count=license_instance_count, days=1)
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)


@pytest.yield_fixture(scope='function')
def install_legacy_license_expired(api_config_pg, license_instance_count):
    log.debug("calling fixture install_legacy_license_expired")

    def apply_license():
        license_info = towerkit.tower.license.generate_license(instance_count=license_instance_count, days=-61)
        api_config_pg.post(license_info)

    apply_license()
    yield apply_license
    api_config_pg.delete()


@pytest.fixture(scope='function')
def install_legacy_license_grace_period(request, api_config_pg, license_instance_count):
    log.debug("calling fixture install_legacy_license_grace_period")

    # Apply license
    license_info = towerkit.tower.license.generate_license(instance_count=license_instance_count, days=-1)
    api_config_pg.post(license_info)
    request.addfinalizer(api_config_pg.delete)


@pytest.fixture(scope='class')
def ansible_ec2_facts(ansible_runner):
    '''This will only work on an ec2 system'''
    contacted = ansible_runner.ec2_facts()
    if len(contacted) > 1:
        log.warning("%d ec2_facts returned, but only returning the first" % len(contacted))
    ec2_facts = contacted.values()[0]
    assert 'ansible_facts' in ec2_facts
    return ec2_facts['ansible_facts']


@pytest.fixture(scope="function")
def inventory_no_free_instances(request, authtoken, api_config_pg, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % fauxfactory.gen_alphanumeric(),
                   description="Random inventory - %s" % fauxfactory.gen_utf8(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Ensure there are at least 5 active hosts
    hosts_pg = obj.get_related('hosts')
    while api_config_pg.get().license_info.instance_count < 5:
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       inventory=obj.id)
        hosts_pg.post(payload)

    # Install a license with instance_count=3
    json = towerkit.tower.license.generate_license(instance_count=3,
                                                   days=-1,
                                                   trial=False,
                                                   company_name=fauxfactory.gen_utf8(),
                                                   contact_name=fauxfactory.gen_utf8(),
                                                   contact_email=fauxfactory.gen_email())
    api_config_pg.post(json)
    request.addfinalizer(api_config_pg.delete)

    return obj


def assert_instance_counts(api_config_pg, api_hosts_pg, license_instance_count, group):
    '''Verify hosts can be added up to the provided 'license_instance_count' variable'''

    # Get API resource /groups/N/hosts
    group_hosts_pg = group.get_related('hosts')

    current_hosts = api_config_pg.get().license_info.current_instances
    while current_hosts <= license_instance_count:
        # Get the /config resource
        conf = api_config_pg.get()

        # Verify instance counts
        assert conf.license_info.current_instances == current_hosts
        assert conf.license_info.free_instances == license_instance_count - current_hosts
        assert conf.license_info.available_instances == license_instance_count
        log.debug("current_instances: {0.license_info.current_instances}, free_instances: "
                  "{0.license_info.free_instances}, available_instances: {0.license_info.available_instances}"
                  .format(conf))

        # Add a host to the inventory group
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       description="host-%s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        # The first 'license_instance_count' hosts should succeed
        if current_hosts < license_instance_count:
            group_hosts_pg.post(payload)
            current_hosts += 1
        # Anything more than 'license_instance_count' will raise a 403
        else:
            with pytest.raises(towerkit.exceptions.LicenseExceeded):
                group_hosts_pg.post(payload)
            with pytest.raises(towerkit.exceptions.LicenseExceeded):
                api_hosts_pg.post(payload)
            break

    # Verify maximum instances
    assert current_hosts == license_instance_count
    assert conf.license_info.current_instances == license_instance_count
    assert conf.license_info.free_instances == 0
    assert conf.license_info.available_instances == license_instance_count


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_No_License(Base_Api_Test):
    '''
    Verify /config behaves as expected when no license is installed
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'no_license')

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3727')
    def test_empty_license_info(self, api_config_pg):
        '''Verify the license_info field is empty'''
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info, indent=4)

    def test_cannot_add_host(self, api_hosts_pg, inventory, group):
        '''Verify that no hosts can be added'''
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       description="host-%s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        group_hosts_pg = group.get_related('hosts')
        with pytest.raises(towerkit.exceptions.LicenseExceeded):
            group_hosts_pg.post(payload)
        with pytest.raises(towerkit.exceptions.LicenseExceeded):
            api_hosts_pg.post(payload)

    def test_can_launch_project_update(self, project_ansible_playbooks_git_nowait):
        '''Verify that project_updates can be launched'''
        job_pg = project_ansible_playbooks_git_nowait.update().wait_until_completed()
        assert job_pg.is_successful, "project_update was unsuccessful - %s" % job_pg

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3937')
    def test_can_launch_inventory_update_but_it_should_fail(self, custom_inventory_source):
        '''Verify that inventory_updates can be launched, but they fail because
        no license is installed.'''
        job_pg = custom_inventory_source.update().wait_until_completed()
        assert job_pg.status == 'failed', "inventory_update was unexpectedly successful - %s" % job_pg
        assert 'CommandError: No Tower license found!' in job_pg.result_stdout

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/3481")
    def test_cannot_launch_job(self, install_basic_license, api_config_pg, job_template):
        '''Verify that job_templates cannot be launched'''
        api_config_pg.delete()
        with pytest.raises(towerkit.exceptions.LicenseExceeded):
            job_template.launch_job()

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3727')
    def test_post_invalid_license(self, api_config_pg, ansible_runner, tower_license_path, invalid_license_json):
        '''Verify that various bogus license formats fail to successfully install'''

        # Assert expected error when issuing a POST with an invalid license
        with pytest.raises(towerkit.exceptions.LicenseInvalid):
            api_config_pg.post(invalid_license_json)

        # Confirm license file not present
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "License file was not expected, but one was found"

        # Assert that no license has been applied
        conf = api_config_pg.get()
        assert conf.license_info == {}, "No license was expected, found %s" % conf.license_info

    def test_post_legacy_license_without_eula_accepted(self, api_config_pg, missing_eula_legacy_license_json):
        '''Verify failure while POSTing a license with no `eula_accepted` attribute.'''

        with pytest.raises(towerkit.exceptions.LicenseInvalid):
            api_config_pg.post(missing_eula_legacy_license_json)

    def test_post_legacy_license_with_rejected_eula(self, api_config_pg, eula_rejected_legacy_license_json):
        '''Verify failure while POSTing a license with `eula_accepted:false` attribute.'''

        with pytest.raises(towerkit.exceptions.LicenseInvalid):
            api_config_pg.post(eula_rejected_legacy_license_json)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3727')
    def test_post_legacy_license(self, api_config_pg, legacy_license_json, ansible_runner, tower_license_path, tower_version_cmp):
        '''Verify that a license can be installed by issuing a POST to the /config endpoint'''
        # Assert that /etc/tower/license does not exist
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "No license file was expected, but one was found"

        # Assert that no license present at /api/v1/config/
        conf = api_config_pg.get()
        assert not conf.is_valid_license, "No license was expected, but one was found"

        # Install the license
        api_config_pg.post(legacy_license_json)

        # Confirm license file is [not] present (depending on version)
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

        # Assert that license present at /api/v1/config/
        conf = api_config_pg.get()
        assert conf.license_info != {}, "License expected, but none found"
        assert conf.license_info.license_key == legacy_license_json['license_key']

        # Remove license
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info, indent=2)

        # Confirm license file is not present
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "No license file was expected, but one was found"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_legacy_license')

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
                            u'rebranding': False}

        # Assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for legacy license: %s." % conf.license_info

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    def test_instance_counts(self, api_config_pg, api_hosts_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > license_instance_count:
            pytest.skip("Skipping test because current_instances > {0}".format(license_instance_count))
        assert_instance_counts(api_config_pg, api_hosts_pg, license_instance_count, group)

    def test_key_visibility_superuser(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_superuser(self, api_config_pg, non_superuser, user_password):
        with self.current_user(non_superuser.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    def test_unable_to_create_scan_job_template(self, api_config_pg, api_job_templates_pg, job_template):
        '''Verify that scan job templates may not be created with a legacy license.'''
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")

        # create playload
        payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random job_template without credentials - %s" % fauxfactory.gen_utf8(),
                       inventory=job_template.inventory,
                       job_type='scan',
                       project=None,
                       credential=job_template.credential,
                       playbook='Default', )

        # post the scan job template and assess response
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, api_job_templates_pg.post, payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Feature system_tracking is not enabled in the active license.'}, \
            "Unexpected API response when attempting to POST a scan job template with a legacy license - %s." % json.dumps(result)

        # attempt to patch job template into scan job template
        payload = dict(job_type='scan', project=None)
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, job_template.patch, **payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Feature system_tracking is not enabled in the active license.'}, \
            "Unexpected API response when attempting to patch a job template into a scan job template with a legacy license - %s." % json.dumps(result)

    @pytest.mark.fixture_args(older_than='1y', granularity='1y')
    def test_unable_to_cleanup_facts(self, cleanup_facts):
        '''Verify that cleanup_facts may not be run with a legacy license.'''

        # wait for cleanup_facts to finish
        job_pg = cleanup_facts.wait_until_completed()

        # assert expected failure
        assert job_pg.status == 'failed', "cleanup_facts job " \
            "unexpectedly passed with a legacy license - %s" % job_pg

        # assert expected stdout
        assert job_pg.result_stdout == "CommandError: The System Tracking " \
            "feature is not enabled for your Tower instance\r\n", \
            "Unexpected stdout when running cleanup_facts with a legacy license."

    def test_unable_to_get_fact_versions(self, host_local):
        '''Verify that GET requests are rejected from fact_versions.'''
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, host_local.get_related, 'fact_versions')
        result = exc_info.value[1]

        assert result == {u'detail': u'Your license does not permit use of system tracking.'}, \
            "Unexpected API response upon attempting to navigate to fact_versions with a legacy license - %s." % json.dumps(result)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3727')
    def test_delete_license(self, api_config_pg, ansible_runner, tower_license_path):
        '''Verify the license_info field is empty after deleting the license'''
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info, indent=2)

        # Confirm license file not present
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "License file was not expected, but one was found"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_License_Warning(Base_Api_Test):
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

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    def test_update_license(self, api_config_pg, legacy_license_json, ansible_runner, tower_license_path, tower_version_cmp):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                before_md5 = result['stat']['md5']

        # Record license_key
        conf = api_config_pg.get()
        before_license_key = conf.license_info.license_key

        # Update the license
        api_config_pg.post(legacy_license_json)

        # Assert that /etc/tower/license was modified (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                after_md5 = result['stat']['md5']
            assert before_md5 != after_md5, "The license file was not modified as expected"

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
class Test_Legacy_License_Grace_Period(Base_Api_Test):
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

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    def test_instance_counts(self, api_config_pg, api_hosts_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > license_instance_count:
            pytest.skip("Skipping test because current_instances > {0}".format(license_instance_count))
        assert_instance_counts(api_config_pg, api_hosts_pg, license_instance_count, group)

    def test_job_launch(self, api_config_pg, job_template):
        '''Verify that job_templates can be launched while there are remaining free_instances'''

        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")
        else:
            job_template.launch_job().wait_until_completed()


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_License_Expired(Base_Api_Test):
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

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        # TODO: If you post a legacy license file that's expired, do we expect the license file
        #       to still get created?
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    def test_host(self, inventory, group):
        '''Verify that no hosts can be added'''
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       description="host-%s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        group_hosts_pg = group.get_related('hosts')
        with pytest.raises(towerkit.exceptions.LicenseExceeded):
            group_hosts_pg.post(payload)

    @pytest.mark.github("https://github.com/ansible/ansible-tower/issues/3483")
    def test_job_launch(self, request, install_basic_license, job_template):
        '''Verify that job_templates cannot be launched'''
        request.getfuncargvalue('install_legacy_license_expired')()
        with pytest.raises(towerkit.exceptions.LicenseExceeded):
            job_template.launch_job().wait_until_completed()

    @pytest.mark.fixture_args(days=1000, older_than='5y', granularity='5y')
    def test_system_job_launch(self, system_job):
        '''Verify that system jobs can be launched'''
        # launch job and assess success
        system_job.wait_until_completed()

        # cleanup_facts jobs will fail if the license does not support it
        if system_job.job_type == 'cleanup_facts':
            assert system_job.status == 'failed', "System job unexpectedly succeeded - %s" % system_job
            assert system_job.result_stdout == "CommandError: The System Tracking feature is not enabled for your Tower instance\r\n"
        # all other system_jobs are expected to succeed
        else:
            assert system_job.is_successful, "System job unexpectedly failed - %s" % system_job

    def test_unable_to_launch_ad_hoc_command(self, request, api_ad_hoc_commands_pg, install_basic_license, host_local, ssh_credential):
        '''Verify that ad hoc commands cannot be launched from all four ad hoc endpoints.'''
        request.getfuncargvalue('install_legacy_license_expired')()

        ad_hoc_commands_pg = api_ad_hoc_commands_pg.get()
        inventory_pg = host_local.get_related('inventory')
        groups_pg = host_local.get_related('groups')
        group_pg = groups_pg.results[0]

        # create payload
        payload = dict(job_type="run",
                       inventory=inventory_pg.id,
                       credential=ssh_credential.id,
                       module_name="ping")

        for endpoint in [inventory_pg, group_pg, host_local]:
            ad_hoc_commands_pg = endpoint.get_related('ad_hoc_commands')
            with pytest.raises(towerkit.exceptions.LicenseExceeded):
                ad_hoc_commands_pg.post(payload), \
                    "Unexpectedly launched an ad_hoc_command with an expired license from %s." % ad_hoc_commands_pg.base_url

    def test_update_license(self, api_config_pg, legacy_license_json, ansible_runner, tower_license_path, tower_version_cmp):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                before_md5 = result['stat']['md5']

        # Record license_key
        conf = api_config_pg.get()
        before_license_key = conf.license_info.license_key

        # Update the license
        api_config_pg.post(legacy_license_json)

        # Record the license md5 and assert file has changed (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                after_md5 = result['stat']['md5']
                assert before_md5 != after_md5, "The license file was not modified as expected"

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
class Test_Legacy_Trial_License(Base_Api_Test):
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

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    def test_instance_counts(self, api_config_pg, api_hosts_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > license_instance_count:
            pytest.skip("Skipping test because current_instances > {0}".format(license_instance_count))
        assert_instance_counts(api_config_pg, api_hosts_pg, license_instance_count, group)

    def test_key_visibility_superuser(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert conf.is_trial_license

    def test_key_visibility_non_superuser(self, api_config_pg, non_superuser, user_password):
        with self.current_user(non_superuser.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    def test_update_license(self, api_config_pg, trial_legacy_license_json, ansible_runner, tower_license_path, tower_version_cmp):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                before_md5 = result['stat']['md5']

        # Record license_key
        conf = api_config_pg.get()
        before_license_key = conf.license_info.license_key

        # Update the license
        api_config_pg.post(trial_legacy_license_json)

        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                after_md5 = result['stat']['md5']

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key
        assert before_license_key != after_license_key, \
            "Expected license_key to change after applying new license, but found old value."

        # Assert that /etc/tower/license was modified
        if tower_version_cmp('3.0.0') < 0:
            assert before_md5 != after_md5, "The license file was not modified as expected"

        # Assert license_key is correct
        expected_license_key = trial_legacy_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Basic_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_basic_license')

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
        assert conf.license_info['license_type'] == 'basic', \
            "Incorrect license_type returned. Expected 'basic,' " \
            "returned %s." % conf.license_info['license_type']

        default_features = {u'surveys': False,
                            u'multiple_organizations': False,
                            u'activity_streams': False,
                            u'ldap': False,
                            u'ha': False,
                            u'system_tracking': False,
                            u'enterprise_auth': False,
                            u'rebranding': False}

        # assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for basic license: %s." % conf.license_info

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    def test_instance_counts(self, api_config_pg, api_hosts_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > license_instance_count:
            pytest.skip("Skipping test because current_instances > {0}".format(license_instance_count))
        assert_instance_counts(api_config_pg, api_hosts_pg, license_instance_count, group)

    def test_key_visibility_superuser(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_superuser(self, api_config_pg, non_superuser, user_password):
        with self.current_user(non_superuser.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    def test_job_launch(self, api_config_pg, job_template):
        '''Verify that job_templates can be launched while there are remaining free_instances'''

        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")
        else:
            job_template.launch_job().wait_until_completed()

    def test_unable_to_create_multiple_organizations(self, api_organizations_pg):
        '''Verify that attempting to create a second organization with a basic license raises a 402.'''
        # check that a default organization already exists
        organizations_pg = api_organizations_pg.get()
        assert organizations_pg.count > 0, "Unexpected number of organizations returned (%s)." % organizations_pg.count

        # post second organization and assess API response
        payload = dict(name="org-%s" % fauxfactory.gen_utf8(),
                       description="Random organization - %s" % fauxfactory.gen_utf8())

        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, api_organizations_pg.post, payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Your Tower license only permits a single organization to exist.'}, \
            "Unexpected response upon trying to create multiple organizations with a basic " \
            "license. %s" % json.dumps(result)

    def test_unable_to_create_survey(self, api_config_pg, job_template_ping, required_survey_spec):
        '''Verify that attempting to create a survey with a basic license raises a 402.'''
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")

        payload = dict(survey_enabled=True)
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, job_template_ping.patch, **payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Feature surveys is not enabled in the active license.'}, \
            "Unexpected API response when attempting to create a survey with a " \
            "basic license - %s." % json.dumps(result)

    def test_unable_to_access_activity_stream(self, api_activity_stream_pg):
        '''Verify that GET requests to api/v1/activity_streams raise 402s.'''
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, api_activity_stream_pg.get)
        result = exc_info.value[1]

        result == {u'detail': u'Your license does not allow use of the activity stream.'}, \
            "Unexpected API response when issuing a GET to api/v1/activity_streams with a basic license - %s." % json.dumps(result)

    def test_unable_to_create_scan_job_template(self, api_config_pg, api_job_templates_pg, job_template):
        '''Verify that scan job templates may not be created with a basic license.'''
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")

        # create playload
        payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random job_template without credentials - %s" % fauxfactory.gen_utf8(),
                       inventory=job_template.inventory,
                       job_type='scan',
                       project=None,
                       credential=job_template.credential,
                       playbook='Default', )

        # post the scan job template and assess response
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, api_job_templates_pg.post, payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Feature system_tracking is not enabled in the active license.'}, \
            "Unexpected API response when attempting to POST a scan job template with a basic license - %s." % json.dumps(result)

        # attempt to patch job template into scan job template
        payload = dict(job_type='scan', project=None)
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, job_template.patch, **payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Feature system_tracking is not enabled in the active license.'}, \
            "Unexpected API response when attempting to patch a job template into a scan job template with a basic license - %s." % json.dumps(result)

    @pytest.mark.fixture_args(older_than='1y', granularity='1y')
    def test_unable_to_cleanup_facts(self, cleanup_facts):
        '''Verify that cleanup_facts may not be run with a basic license.'''

        # wait for cleanup_facts to finish
        job_pg = cleanup_facts.wait_until_completed()

        # assert expected failure
        assert job_pg.status == 'failed', "cleanup_facts job " \
            "unexpectedly passed with a basic license - %s" % job_pg

        # assert expected stdout
        assert job_pg.result_stdout == "CommandError: The System Tracking " \
            "feature is not enabled for your Tower instance\r\n", \
            "Unexpected stdout when running cleanup_facts with a basic license."

    def test_unable_to_get_fact_versions(self, host_local):
        '''Verify that GET requests are rejected from fact_versions.'''
        exc_info = pytest.raises(towerkit.exceptions.PaymentRequired, host_local.get_related, 'fact_versions')
        result = exc_info.value[1]

        assert result == {u'detail': u'Your license does not permit use of system tracking.'}, \
            "Unexpected JSON response upon attempting to navigate to fact_versions with a basic license - %s." % json.dumps(result)

    def test_upgrade_to_enterprise(self, enterprise_license_json, api_config_pg, ansible_runner, tower_license_path, tower_version_cmp):
        '''Verify that a basic license can get upgraded to an enterprise license.'''

        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(enterprise_license_json)

        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                after_md5 = result['stat']['md5']

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key

        # Assert that /etc/tower/license was modified
        if tower_version_cmp('3.0.0') < 0:
            assert before_md5 != after_md5, "The license file was not modified as expected"

        # Assert license_key is correct
        expected_license_key = enterprise_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)

        # Confirm enterprise license present
        conf = api_config_pg.get()
        assert conf.license_info['license_type'] == 'enterprise', \
            "Incorrect license_type returned. Expected 'enterprise,' " \
            "returned %s." % conf.license_info['license_type']

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3727')
    def test_delete_license(self, api_config_pg, ansible_runner, tower_license_path):
        '''Verify the license_info field is empty after deleting the license'''
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info, indent=2)

        # Confirm license file not present
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "License file was not expected, but one was found"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Enterprise_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

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
                            u'rebranding': True}

        # assess default features
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for enterprise license: %s." % conf.license_info

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    def test_instance_counts(self, api_config_pg, api_hosts_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > license_instance_count:
            pytest.skip("Skipping test because current_instances > {0}".format(license_instance_count))
        assert_instance_counts(api_config_pg, api_hosts_pg, license_instance_count, group)

    def test_key_visibility_superuser(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_superuser(self, api_config_pg, non_superuser, user_password):
        with self.current_user(non_superuser.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    def test_job_launch(self, api_config_pg, job_template):
        '''Verify that job_templates can be launched while there are remaining free_instances'''
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")
        else:
            job_template.launch_job().wait_until_completed()

    def test_post_multiple_organizations(self, api_organizations_pg):
        '''Verify that multiple organizations may exist with an enterprise license.'''
        # create second organization
        payload = dict(name="org-%s" % fauxfactory.gen_utf8(),
                       description="Random organization - %s" % fauxfactory.gen_utf8())
        api_organizations_pg.post(payload)

        # assert multiple organizations exist
        organizations_pg = api_organizations_pg.get()
        assert organizations_pg.count > 1, "Multiple organizations are supposed" \
            "to exist, but do not. Instead, only %s exist." % api_organizations_pg.count

    def test_create_survey(self, api_config_pg, job_template_ping, required_survey_spec):
        '''Verify that surveys may be created with an enterprise license.'''
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")

        job_template_ping.patch(survey_enabled=True)

        # post survey
        survey_spec = job_template_ping.get_related('survey_spec')
        survey_spec.post(required_survey_spec)

        # assert survey created
        survey_spec.get()
        assert survey_spec.name == required_survey_spec['name']

    def test_activity_streams(self, api_activity_stream_pg):
        '''Verify that GET requests to api/v1/activity_streams are allowed with an enterprise license.'''
        api_activity_stream_pg.get()

    def test_post_scan_job_template(self, api_config_pg, api_job_templates_pg, ssh_credential, host_local):
        '''Verifies that scan job templates may be created with an enterprise license.'''
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")

        # create payload
        payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random scan job_template - %s" % fauxfactory.gen_utf8(),
                       inventory=host_local.inventory,
                       job_type='scan',
                       project=None,
                       credential=ssh_credential.id,
                       playbook='Default', )

        # post scan_job template
        api_job_templates_pg.post(payload)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/4157')
    def test_launch_scan_job(self, api_config_pg, api_job_templates_pg, ssh_credential, host_local):
        '''Verifies that scan jobs may be launched with an enterprise license.'''
        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")

        # create payload
        payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random scan job_template - %s" % fauxfactory.gen_utf8(),
                       inventory=host_local.inventory,
                       job_type='scan',
                       project=None,
                       credential=ssh_credential.id,
                       playbook='Default', )

        # post scan_job template
        scan_job_template_pg = api_job_templates_pg.post(payload)

        # launch the job_template and wait for completion
        job_pg = scan_job_template_pg.launch().wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    @pytest.mark.fixture_args(older_than='1y', granularity='1y')
    def test_able_to_cleanup_facts(self, cleanup_facts):
        '''Verifies that cleanup_facts may be run with an enterprise license.'''

        # wait for cleanup_facts to finish
        job_pg = cleanup_facts.wait_until_completed()

        # assert expected failure
        assert job_pg.is_successful, "cleanup_facts job unexpectedly failed " \
            "with an enterprise license - %s" % job_pg

    def test_able_to_get_facts(self, scan_job_with_status_completed):
        '''Verify that that enterprise license users can GET fact endpoints.'''
        host_pg = scan_job_with_status_completed.get_related('inventory').get_related('hosts').results[0]

        # test navigating to fact pages
        fact_versions_pg = host_pg.get_related('fact_versions')
        for fact_version in fact_versions_pg.results:
            fact_version.get_related('fact_view')

    def test_downgrade_to_basic(self, basic_license_json, api_config_pg, ansible_runner, tower_license_path, tower_version_cmp):
        '''Verify that an enterprise license can get downgraded to a basic license by posting to api_config_pg.'''
        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(basic_license_json)

        # Record license_key
        conf = api_config_pg.get()
        after_license_key = conf.license_info.license_key

        # Record the license md5 (if running older version of tower)
        if tower_version_cmp('3.0.0') < 0:
            contacted = ansible_runner.stat(path=tower_license_path)
            for result in contacted.values():
                after_md5 = result['stat']['md5']

        # Assert that /etc/tower/license was modified
        if tower_version_cmp('3.0.0') < 0:
            assert before_md5 != after_md5, "The license file was not modified as expected"

        # Assess license type
        conf = api_config_pg.get()
        assert conf.license_info['license_type'] == 'basic', \
            "Incorrect license_type returned. Expected 'basic,' " \
            "returned %s." % conf.license_info['license_type']

        # Assert license_key is correct
        expected_license_key = basic_license_json['license_key']
        assert after_license_key == expected_license_key, \
            "Unexpected license_key. Expected %s, found %s" % (expected_license_key, after_license_key)

    @pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3727')
    def test_delete_license(self, api_config_pg, ansible_runner, tower_license_path):
        '''Verify the license_info field is empty after deleting the license'''
        api_config_pg.delete()
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info, indent=2)

        # Confirm license file not present
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "License file was not expected, but one was found"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Enterprise_License_Expired(Base_Api_Test):
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

    def test_license_file(self, api_config_pg, tower_version_cmp, ansible_runner, tower_license_path):
        '''Verify that tower license file is [not] created (depending on tower version)'''
        # TODO: If an expired enterprise license is posted, do we expected a license file
        #       to get created?
        contacted = ansible_runner.stat(path=tower_license_path)
        if tower_version_cmp('3.0.0') < 0:
            for result in contacted.values():
                assert result['stat']['exists'], "License file was expected, but none was found"
        else:
            for result in contacted.values():
                assert not result['stat']['exists'], "No license file was expected, but one was found"

    @pytest.mark.fixture_args(days=1000, older_than='5y', granularity='5y')
    def test_system_job_launch(self, system_job):
        '''Verify that system jobs can be launched'''
        # launch job and assess success
        system_job.wait_until_completed()

        assert system_job.is_successful, "System job unexpectedly failed - %s" % system_job
