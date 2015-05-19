'''
 == Demo Tests ==
 [X] Ensure instance counts are correct
 [X] Add systems and verify counts adjust
 [X] Manually add a system to exceed demo instance max
 [ ] Import inventory that would exceed instance_max
 [ ] Disable existing hosts and verify instance counts

 == Demo Tests ==
 [X] Verify a valid license has no warning or expired
 [X] Verify a valid license has expected system counts
 [X] Add systems and verify instance_counts
 [X] Exceed instance_max manually and via inventory sync
 [ ] Disable existing hosts and verify instance counts
 [ ] Test upgrading license ... does it increase instance_count?
 [ ] Test date_warning=False, date_warning=True, and date_expired=True
'''

'''
# Test No License
[X] Test that config.license_info is empty before license is added
[X] Test that you cannot add hosts without a license
[X] Test can't launch job without license
[X] Tests that invalid licenses get rejected
[X] Test that if you post a legacy licenses with no EULA that the post gets rejected
[X] Tests that if you post a legacy licenses and reject the EULA that the post gets rejected
[X] Tests that you can post a legacy license

# Test Legacy License
[X] Test metadata
[N] Verify expected features
[X] Verify that hosts can be added to license maximum
[X] Verify that license_key is visible to admin user
[X] Verify that license_key is not visible to non-admin users
[?] Test cannot launch scan jobs
[N] Test cannot create scan job templates
[?] Test cannot run cleanup_facts
[?] Test cannot GET single_fact endpoints
[?] Test cannot GET fact_versions endpoints
[?] Test cannot GET fact_compare endpoints

# Test Legacy License Warning
[X] Test metadata
[X] Test that you can update the license by posting a new one

# Test Legacy License Grace Period
[X] Test metadata
[X] Test that hosts can be added to license maximum
[X] Test that jobs can be launched if there are remaining free instances
[X] Test that you cannot launch jobs if there are no free instances

# Test Legacy License Expired
[X] Test metadata
[X] Tests that no hosts can be added
[X] Test that job templates cannot be launched
[N] Test that ad hoc commands cannot be launched from all four endpoints
[N] Test that system jobs can be launched
[X] Test that you can post a new license to the api/v1/config endpoint

# Test Legacy Trial License
[X] Test metadata
[X] Test that you can add hosts up to limit
[X] Test that admins can see the product key
[X] Test that non-admins cannot see the product key
[X] Test that you can update the license by posting to api/v1/config

# Test Basic License
[N] Test metadata
[N] Test default features
[X] Test can add hosts to limit
[X] Test admin can see license key
[X] Test non-admin cannot see license key
[X] Test can launch jobs
[X] Verify that job_templates cannot be launched when free_instances < 0
[?] Test cannot post multiple organizations
[N] Test cannot create surveys
[?] Test cannot issue GET requests to randomly selected activity stream endpoints
[] Test cannot promote secondary
[N] Test cannot register secondary
[] Test that LDAP is disabled
[?] Test cannot launch scan jobs
[N] Test cannot create scan JT
[?] Test cannot launch cleanup_facts
[?] Test cannot GET single_fact endpoints
[?] Test cannot GET fact_versions endpoints
[?] Test cannot GET fact_compare endpoints

# Test Enterprise License
[N] Test metadata
[N] Test default features
[X] Test can add hosts to limit
[X] Test admin can see key
[X] Test non-admins cannot see keys
[X] Test can launch job
[X] Verify that job_templates cannot be launched when free_instances < 0
[N] Test can post multiple organizations
[N] Test can create surveys
[?] Test can issue GET requests to randomly selected activity stream endpoints
[] Test can promote secondary
[N] Test can register secondary
[] Test that LDAP is enabled
[N] Test can launch scan jobs
[N] Test can create scan JT
[N] Test can launch cleanup_facts
[?] Test can GET single_fact endpoints
[?] Test can GET fact_versions endpoints
[?] Test can GET fact_compare endpoints

# Test Downgrade from Enterprise to Basic
[N] Test downgrade Enterprise to Basic
[N] Test meta
[N] Test mongodb deactivated

# Test Upgrade from Basic to Enterprise
[N] Test upgrade Basic to Enterprise
[N] Test meta
[?] Test mongodb activated

# Test features - A basic license with all feature enabled
'''

import json
import pytest
import logging
import fauxfactory
import common.tower.license
import common.exceptions
from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope='class')
def license_instance_count(request):
    '''Number of host instances permitted by the license'''
    return 20


@pytest.fixture(scope='class')
def install_trial_legacy_license(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_trial_legacy_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31, trial=True)
    # Using ansible, copy the license to the target system
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='function')
def legacy_license_json(request, license_instance_count):
    return common.tower.license.generate_license(instance_count=license_instance_count,
                                                 days=31,
                                                 company_name=fauxfactory.gen_utf8(),
                                                 contact_name=fauxfactory.gen_utf8(),
                                                 contact_email="%s@example.com" % fauxfactory.gen_utf8())


@pytest.fixture(scope='function')
def basic_license_json(request, license_instance_count):
    return common.tower.license.generate_license(instance_count=license_instance_count,
                                                 days=31,
                                                 company_name=fauxfactory.gen_utf8(),
                                                 contact_name=fauxfactory.gen_utf8(),
                                                 contact_email="%s@example.com" % fauxfactory.gen_utf8(),
                                                 license_type="basic")


@pytest.fixture(scope='function')
def enterprise_license_json(request, license_instance_count):
    return common.tower.license.generate_license(instance_count=license_instance_count,
                                                 days=31,
                                                 company_name=fauxfactory.gen_utf8(),
                                                 contact_name=fauxfactory.gen_utf8(),
                                                 contact_email="%s@example.com" % fauxfactory.gen_utf8(),
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
    return common.tower.license.generate_license(instance_count=license_instance_count,
                                                 days=31,
                                                 trial=True,
                                                 company_name=fauxfactory.gen_utf8(),
                                                 contact_name=fauxfactory.gen_utf8(),
                                                 contact_email="%s@example.com" % fauxfactory.gen_utf8())


@pytest.fixture(scope='class')
def install_legacy_license(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_legacy_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31)
    # Using ansible, copy the license to the target system
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_basic_license(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_legacy_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31, license_type="basic")
    # Using ansible, copy the license to the target system
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_enterprise_license(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_legacy_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31, license_type="enterprise")
    # Using ansible, copy the license to the target system
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_legacy_license_warning(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_legacy_license_warning")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=1)
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_legacy_license_expired(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_legacy_license_expired")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=-61)
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_legacy_license_grace_period(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_legacy_license_grace_period")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=-1)
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def ansible_ec2_facts(ansible_runner):
    '''This will only work on an ec2 system'''
    contacted = ansible_runner.ec2_facts()
    if len(contacted) > 1:
        log.warning("%d ec2_facts returned, but only returning the first" % len(contacted))
    ec2_facts = contacted.values()[0]
    assert 'ansible_facts' in ec2_facts
    return ec2_facts['ansible_facts']


@pytest.fixture(scope='class')
def ami_id(ansible_ec2_facts):
    return ansible_ec2_facts['ansible_ec2_ami_id']


@pytest.fixture(scope='class')
def instance_id(ansible_ec2_facts):
    return ansible_ec2_facts['ansible_ec2_instance_id']


@pytest.fixture(scope='class')
def install_legacy_license_aws(request, ansible_runner, license_instance_count, ami_id, instance_id, tower_aws_path):
    log.debug("calling fixture install_legacy_license_aws")
    fname = common.tower.license.generate_aws_file(instance_count=license_instance_count, ami_id=ami_id, instance_id=instance_id)
    contacted = ansible_runner.copy(src=fname, dest=tower_aws_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope="function", params=['org_admin', 'org_user', 'anonymous_user'])
def non_admin_user(request):
    return request.getfuncargvalue(request.param)


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
    json = common.tower.license.generate_license(instance_count=3,
                                                 days=-1,
                                                 trial=False,
                                                 company_name=fauxfactory.gen_utf8(),
                                                 contact_name=fauxfactory.gen_utf8(),
                                                 contact_email="%s@example.com" % fauxfactory.gen_utf8())
    api_config_pg.post(json)

    return obj


def assert_instance_counts(api_config_pg, license_instance_count, group):
    '''Verify hosts can be added up to the provided 'license_instance_count' variable'''

    # Get API resource /groups/N/hosts
    group_hosts_pg = group.get_related('hosts')

    current_hosts = 0
    while current_hosts <= license_instance_count:
        # Get the /config resource
        conf = api_config_pg.get()

        # Verify instance counts
        assert conf.license_info.current_instances == current_hosts
        assert conf.license_info.free_instances == \
            license_instance_count - current_hosts
        assert conf.license_info.available_instances == license_instance_count
        print "current_instances:%s, free_instances:%s, available_instances:%s" % \
            (conf.license_info.current_instances, conf.license_info.free_instances,
             conf.license_info.available_instances)

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
            with pytest.raises(common.exceptions.LicenseExceeded_Exception):
                group_hosts_pg.post(payload)
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
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license')

    def test_empty_license_info(self, api_config_pg):
        '''Verify the license_info field is empty'''
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info, indent=4)

    def test_cannot_add_host(self, inventory, group):
        '''Verify that no hosts can be added'''
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       description="host-%s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        group_hosts_pg = group.get_related('hosts')
        with pytest.raises(common.exceptions.Forbidden_Exception):
            group_hosts_pg.post(payload)

    def test_cannot_launch_job(self, job_template):
        '''Verify that job_templates cannot be launched'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()

    def test_post_invalid_license(self, api_config_pg, ansible_runner, tower_license_path, invalid_license_json):
        '''Verify that various bogus license formats fail to successfully install'''

        # Assert expected error when issuing a POST with an invalid license
        with pytest.raises(common.exceptions.LicenseInvalid_Exception):
            api_config_pg.post(invalid_license_json)

        # Assert that /etc/tower/license does not exist
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "No license was expected, but one was found"

    def test_post_legacy_license_without_eula_accepted(self, api_config_pg, missing_eula_legacy_license_json):
        '''Verify failure while POSTing a license with no `eula_accepted` attribute.'''

        with pytest.raises(common.exceptions.LicenseInvalid_Exception):
            api_config_pg.post(missing_eula_legacy_license_json)

    def test_post_legacy_license_with_rejected_eula(self, api_config_pg, eula_rejected_legacy_license_json):
        '''Verify failure while POSTing a license with `eula_accepted:false` attribute.'''

        with pytest.raises(common.exceptions.LicenseInvalid_Exception):
            api_config_pg.post(eula_rejected_legacy_license_json)

    def test_post_legacy_license(self, api_config_pg, legacy_license_json, ansible_runner, tower_license_path):
        '''Verify that a license can be installed by issuing a POST to the /config endpoint'''
        # Assert that /etc/tower/license does not exist
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "No license was expected, but one was found"

        # Install the license
        api_config_pg.post(legacy_license_json)

        # Assert that /etc/tower/license was created
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert result['stat']['exists'], "A license was not succesfully installed to %s" % (tower_license_path)


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_AWS_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_legacy_license_aws')

    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.license_info)

        # Assert NOT Demo mode
        assert not conf.is_demo_license

        # Assert AWS info
        assert conf.is_aws_license

        # Assert the license is valid
        assert conf.is_valid_license

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert not conf.license_info.date_warning

        # Assess license type
        assert conf.license_info['license_type'] == 'legacy', \
            "Incorrect license_type returned. Expected 'legacy,' " \
            "returned %s." % conf.license_info['license_type']

    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    @pytest.mark.trello('https://trello.com/c/Llol9BCJ')
    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > 0:
            pytest.skip("Skipping test because current_instances > 0")
        assert_instance_counts(api_config_pg, license_instance_count, group)

    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_key' in conf.license_info

    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_update_license(self, api_config_pg, legacy_license_json, ansible_runner, tower_license_path, tower_aws_path):
        '''Verify that a regular license can be installed by issuing a POST to
        the /config endpoint.  The regular license should win out over the AWS
        license.
        '''
        # Assert that /etc/tower/aws exists
        contacted = ansible_runner.stat(path=tower_aws_path)
        for result in contacted.values():
            assert result['stat']['exists'], "A AWS license was expected, but none were found. %s" % result

        # Assert that /etc/tower/license does not exist
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "No license was expected, but one was found. %s" % result

        # Record the license md5
        contacted = ansible_runner.stat(path=tower_aws_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(legacy_license_json)

        # Assert that /etc/tower/license was created
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert result['stat']['exists'], "A license was expected, but none were found. %s" % result
            after_md5 = result['stat']['md5']

        # Assert the license file changed
        assert before_md5 != after_md5, "The license file was not modified as expected"

        # Assert the current license is NOT an aws license
        conf = api_config_pg.get()
        assert not conf.is_aws_license, "After installing a regular license, the /config endpoint reports that a AWS license is active. %s" \
            % json.dumps(conf.json, indent=4)


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_legacy_license')

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

    def test_default_license_features(self, api_config_pg):
        '''Tests legacy default features.'''
        default_features = {u'surveys': True,
                            u'multiple_organizations': True,
                            u'activity_streams': True,
                            u'ldap': True,
                            u'ha': True,
                            u'system_tracking': False}

        # assess default features
        conf = api_config_pg.get()
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for legacy license: %s." % conf.license_info

    @pytest.mark.trello('https://trello.com/c/Llol9BCJ')
    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > 0:
            pytest.skip("Skipping test because current_instances > 0")
        assert_instance_counts(api_config_pg, license_instance_count, group)

    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    @pytest.mark.skipif(True, reason="Not yet implemented.")
    def test_launch_scan_job(self, job_template_with_job_type_scan):
        '''Verify that scan jobs may not be run with a legacy license.'''
        launch_pg = job_template_with_job_type_scan.get_related('launch')

        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, launch_pg.post)
        result = exc_info.value[1]

        # FIXME
        assert result == {}

    def test_post_scan_job_template(self, api_job_templates_pg, ssh_credential, host_local):
        '''Verify that scan job templates may not be created with a legacy license.'''
        # create playload
        payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random job_template without credentials - %s" % fauxfactory.gen_utf8(),
                       inventory=host_local.get_related('inventory').id,
                       job_type='scan',
                       project=None,
                       credential=ssh_credential.id,
                       playbook='Default', )

        # post the scan job template and assess response
        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, api_job_templates_pg.post, payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Feature system_tracking is not enabled in the active license'}, \
            "Unexpected API response when attempting to POST a scan job template with a legacy license - %s." % json.dumps(result)

    @pytest.mark.trello('https://trello.com/c/Sz50XpNl')
    def test_run_cleanup_facts(self, cleanup_facts_template):
        '''Verify that cleanup_facts may not be run with a legacy license.'''
        launch_pg = cleanup_facts_template.get_related('launch')

        # launch cleanup_facts and assess API response
        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, launch_pg.post)
        result = exc_info.value[1]

        # FIXME
        assert result == {}

    @pytest.mark.skipif(True, reason="Not yet implemented.")
    def test_get_with_legacy_license(self, host_local):
        '''Verify that GET requests are rejected from all fact endpoints with legacy license.'''
        inventory_pg = host_local.get_related('inventory')
        group_pg = host_local.get_related('group')

        # Check that GET requests rejected
        inventory_pg.get_related('single_fact')
        group_pg.get_related('single_fact')
        host_local.get_related('single_fact')
        host_local.get_related('fact_versions')


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_License_Warning(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_legacy_license_warning')

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

    def test_update_license(self, api_config_pg, legacy_license_json, ansible_runner, tower_license_path):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(legacy_license_json)

        # Assert that /etc/tower/license was modified
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']
        assert before_md5 != after_md5, "The license file was not modified as expected"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_License_Grace_Period(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_legacy_license_grace_period')

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

    @pytest.mark.trello('https://trello.com/c/Llol9BCJ')
    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > 0:
            pytest.skip("Skipping test because current_instances > 0")
        assert_instance_counts(api_config_pg, license_instance_count, group)

    def test_job_launch(self, api_config_pg, job_template):
        '''Verify that job_templates can be launched while there are remaining free_instances'''

        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")
        else:
            job_template.launch_job()

    def FIXME_test_job_launch_hosts_exceeded(self, inventory_no_free_instances, job_template):
        '''Verify that job_templates cannot be launched when free_instances < 0'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_License_Expired(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_legacy_license_expired')

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

    def test_host(self, inventory, group):
        '''Verify that no hosts can be added'''
        payload = dict(name="host-%s" % fauxfactory.gen_utf8().replace(':', ''),
                       description="host-%s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory)
        group_hosts_pg = group.get_related('hosts')
        with pytest.raises(common.exceptions.Forbidden_Exception):
            group_hosts_pg.post(payload)

    def test_job_launch(self, job_template):
        '''Verify that job_templates cannot be launched'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()

    def test_system_job_launch(self, system_job_template):
        '''Verify that system job templates can be launched'''
        launch_pg = system_job_template.get_related("launch")
        launch_pg.post()

    def test_ad_hoc_command_launch(self, api_ad_hoc_commands_pg, host_local, ssh_credential):
        '''Verify that ad hoc commands cannot be launched from all four ad hoc endpoints.'''
        ad_hoc_commands_pg = api_ad_hoc_commands_pg.get()
        inventory_pg = host_local.get_related('inventory')
        groups_pg = host_local.get_related('groups')
        group_pg = groups_pg.results[0]

        # create payload
        payload = dict(job_type="run",
                       inventory=inventory_pg.id,
                       credential=ssh_credential.id,
                       module_name="ping")

        # from api/v1/ad_hoc_commands
        with pytest.raises(common.exceptions.Forbidden_Exception):
            ad_hoc_commands_pg.post(payload), \
                "ad hoc command launched with expired license from api/v1/ad_hoc_commands."

        # from api/v1/inventories/{ID}/ad_hoc_commands
        ad_hoc_commands_pg = inventory_pg.get_related('ad_hoc_commands')
        with pytest.raises(common.exceptions.Forbidden_Exception):
            ad_hoc_commands_pg.post(payload), \
                "ad hoc command launched with expired license from api/v1/inventories/{ID}/ad_hoc_commands."

        # from api/v1/groups/{ID}/ad_hoc_commands
        ad_hoc_commands_pg = group_pg.get_related('ad_hoc_commands')
        with pytest.raises(common.exceptions.Forbidden_Exception):
            ad_hoc_commands_pg.post(payload), \
                "ad hoc command launched with expired license from api/v1/groups/{ID}/ad_hoc_commands."

        # from api/v1/hosts/{ID}/ad_hoc_commands
        ad_hoc_commands_pg = host_local.get_related('ad_hoc_commands')
        with pytest.raises(common.exceptions.Forbidden_Exception):
            ad_hoc_commands_pg.post(payload), \
                "ad hoc command launched with expired license from api/v1/hosts/{ID}/ad_hoc_commands."

    def test_update_license(self, api_config_pg, legacy_license_json, ansible_runner, tower_license_path):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(legacy_license_json)

        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']

        # Assert that /etc/tower/license was modified
        assert before_md5 != after_md5, "The license file was not modified as expected"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Legacy_Trial_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_trial_legacy_license')

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

    @pytest.mark.trello('https://trello.com/c/Llol9BCJ')
    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > 0:
            pytest.skip("Skipping test because current_instances > 0")
        assert_instance_counts(api_config_pg, license_instance_count, group)

    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert conf.is_trial_license

    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    def test_update_license(self, api_config_pg, trial_legacy_license_json, ansible_runner, tower_license_path):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(trial_legacy_license_json)

        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']

        # Assert that /etc/tower/license was modified
        assert before_md5 != after_md5, "The license file was not modified as expected"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Basic_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_basic_license')

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

    def test_default_license_features(self, api_config_pg):
        '''Tests basic license default features.'''
        default_features = {u'surveys': False,
                            u'multiple_organizations': False,
                            u'activity_streams': False,
                            u'ldap': False,
                            u'ha': False,
                            u'system_tracking': False}

        # assess default features
        conf = api_config_pg.get()
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for basic license: %s." % conf.license_info

    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > 0:
            pytest.skip("Skipping test because current_instances > 0")
        assert_instance_counts(api_config_pg, license_instance_count, group)

    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    def test_job_launch(self, api_config_pg, job_template):
        '''Verify that job_templates can be launched while there are remaining free_instances'''

        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")
        else:
            job_template.launch_job()

    def FIXME_test_job_launch_hosts_exceeded(self, inventory_no_free_instances, job_template):
        '''Verify that job_templates cannot be launched when free_instances < 0'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()

    def test_post_multiple_organizations(self, api_organizations_pg):
        '''Verify that attempting to create a second organization with a basic license raises a 402.'''
        # check that a default organization already exists
        organizations_pg = api_organizations_pg.get()
        assert organizations_pg.count == 1, "Unexpected number of organizations returned (%s), but expecting one." % organizations_pg.count

        # post second organization and assess API response
        payload = dict(name="org-%s" % fauxfactory.gen_utf8(),
                       description="Random organization - %s" % fauxfactory.gen_utf8())

        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, api_organizations_pg.post, payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Your Tower license only permits a single organization to exist.'}, \
            "Unexpected repsonse upon trying to create multiple organizations with a basic " \
            "license. %s" % json.dumps(result)

    def test_create_survey(self, job_template_ping, required_survey_spec):
        '''Verify that attempting to create a survey with a basic license raises a 402.'''
        job_template_ping.patch(survey_enabled=True)

        # post a survey and assess API response
        survey_spec = job_template_ping.get_related('survey_spec')
        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, survey_spec.post)
        result = exc_info.value[1]

        assert result == {u'detail': u'Your license does not allow adding surveys.'}, \
            "Unexpected API response when attempting to create a survey with a basic license - %s." % json.dumps(result)

    def test_activity_streams(self, api_activity_stream_pg):
        '''Verify that GET requests to api/v1/activity_streams raise 402s.'''
        # Issue a GET to api/v1/activity_streams and assess the response
        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, api_activity_stream_pg.get)
        result = exc_info.value[1]

        result == {u'detail': u'Your license does not allow use of the activity stream.'}, \
            "Unexpected API response when issuing a GET to api/v1/activity_streams with a basic license - %s." % json.dumps(result)

    def test_register_secondary(self, ansible_runner):
        '''Verifies that attempting to register a secondary with a basic license raises a license error.'''
        # attempt to register new instance
        contacted = ansible_runner.shell('tower-manage register_instance --hostname foo --secondary')
        result = contacted.values()[0]

        # assess output
        assert result['stderr'] == 'CommandError: Your Tower license does not permit creation of secondary instances.', \
            "Unexpected stderr when attempting to register secondary with basic license: %s." % result['stderr']

    @pytest.mark.skipif(True, reason="Not yet implemented.")
    def test_launch_scan_job(self, job_template_with_job_type_scan):
        '''Verify that scan jobs may not be run with a basic license.'''
        launch_pg = job_template_with_job_type_scan.get_related('launch')

        # launch the scan job and assess the response
        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, launch_pg.post)
        result = exc_info.value[1]

        # FIXME
        assert result == {}

    def test_post_scan_job_template(self, api_job_templates_pg, ssh_credential, host_local):
        '''Verify that scan job templates may not be created with a basic license.'''
        # create playload
        payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random job_template without credentials - %s" % fauxfactory.gen_utf8(),
                       inventory=host_local.get_related('inventory').id,
                       job_type='scan',
                       project=None,
                       credential=ssh_credential.id,
                       playbook='Default', )

        # post the scan job template and assess the response
        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, api_job_templates_pg.post, payload)
        result = exc_info.value[1]

        assert result == {u'detail': u'Feature system_tracking is not enabled in the active license'}, \
            "Unexpected API response when attempting to POST a scan job template with a legacy license - %s." % json.dumps(result)

    @pytest.mark.trello('https://trello.com/c/Sz50XpNl')
    def test_run_cleanup_facts(self, cleanup_facts_template):
        '''Verify that cleanup_facts may not be run with a basic license.'''
        launch_pg = cleanup_facts_template.get_related('launch')

        # launch cleanup_facts and assess the response
        exc_info = pytest.raises(common.exceptions.PaymentRequired_Exception, launch_pg.post)
        result = exc_info.value[1]

        # FIXME
        assert result == {}

    @pytest.mark.skipif(True, reason="Not yet implemented.")
    def test_get_with_basic_license(self, host_local):
        '''Verify that GET requests are rejected from all fact endpoints with a basic license.'''
        inventory_pg = host_local.get_related('inventory')
        group_pg = host_local.get_related('group')

        # Check that GET requests rejected
        inventory_pg.get_related('single_fact')
        group_pg.get_related('single_fact')
        host_local.get_related('single_fact')
        host_local.get_related('fact_versions')


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Enterprise_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_enterprise_license')

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

    def test_default_license_features(self, api_config_pg):
        '''Tests enterprise default features.'''
        default_features = {u'surveys': True,
                            u'multiple_organizations': True,
                            u'activity_streams': True,
                            u'ldap': True,
                            u'ha': True,
                            u'system_tracking': True}

        # assess default features
        conf = api_config_pg.get()
        assert conf.license_info['features'] == default_features, \
            "Unexpected features returned for basic license: %s." % conf.license_info

    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info.current_instances > 0:
            pytest.skip("Skipping test because current_instances > 0")
        assert_instance_counts(api_config_pg, license_instance_count, group)

    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_key' not in conf.license_info

    def test_job_launch(self, api_config_pg, job_template):
        '''Verify that job_templates can be launched while there are remaining free_instances'''

        conf = api_config_pg.get()
        if conf.license_info.free_instances < 0:
            pytest.skip("Unable to test because there are no free_instances remaining")
        else:
            job_template.launch_job()

    def FIXME_test_job_launch_hosts_exceeded(self, inventory_no_free_instances, job_template):
        '''Verify that job_templates cannot be launched when free_instances < 0'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()

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

    def test_create_survey(self, job_template_ping, required_survey_spec):
        '''Verify that surveys may be created with an enterprise license.'''
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

    def test_register_secondary(self, ansible_runner):
        '''
        Tests that attempting to register a secondary with an enterprise license does not raise a
        license error.
        '''
        # attempt to register new instance
        contacted = ansible_runner.shell('tower-manage register_instance --hostname foo --secondary')
        result = contacted.values()[0]

        # assess output
        assert 'CommandError: Instance already registered with a different hostname' in result['stderr'], \
            "Unexpected stderr when attempting to register secondary with basic license: %s." % result['stderr']

    def test_launch_scan_job(self, job_template_with_job_type_scan):
        '''Verifies that scan jobs may be launched with an enterprise license.'''
        # launch the job_template and wait for completion
        job_pg = job_template_with_job_type_scan.launch().wait_until_completed()

        # assert success
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

    def test_post_scan_job_template(self, api_job_templates_pg, ssh_credential, host_local):
        '''Verifies that scan job templates may be created with an enterprise license.'''
        # create payload
        payload = dict(name="job_template-%s" % fauxfactory.gen_utf8(),
                       description="Random job_template without credentials - %s" % fauxfactory.gen_utf8(),
                       inventory=host_local.get_related('inventory').id,
                       job_type='scan',
                       project=None,
                       credential=ssh_credential.id,
                       playbook='Default', )

        # post job template
        api_job_templates_pg.post(payload)

    def test_run_cleanup_facts(self, cleanup_facts_template):
        '''Verifies that cleanup_facts may be run with an enterprise license.'''
        launch_pg = cleanup_facts_template.get_related('launch')

        # post job and check that job completes successfully
        job_pg = launch_pg.post()
        assert job_pg.is_successful, "Unexpected job status upon launching cleanup_facts with" \
            "an enterprise license - %s." % job_pg

    @pytest.mark.skipif(True, reason="Not yet implemented.")
    def test_get_with_enterprise_license(self, host_local):
        '''Verify that GET requests are accepted from all fact endpoints with an enterprise license.'''
        inventory_pg = host_local.get_related('inventory')
        group_pg = host_local.get_related('group')

        # Check that GET requests rejected
        inventory_pg.get_related('single_fact')
        group_pg.get_related('single_fact')
        host_local.get_related('single_fact')
        host_local.get_related('fact_versions')


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Downgrade_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_enterprise_license')

    def test_downgrade_from_enterprise_to_basic(self, basic_license_json, api_config_pg, ansible_runner, tower_license_path):
        '''That an enterprise license can get downgraded to a basic license by posting to api_config_pg.'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(basic_license_json)

        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']

        # Assert that /etc/tower/license was modified
        assert before_md5 != after_md5, "The license file was not modified as expected"

    def test_metadata(self, api_config_pg):
        '''Tests that api/v1/config reflects the new license.'''
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

    def test_mongodb_deactivated(self, ansible_runner):
        '''Tests that MongoDB is deactivated.'''
        # check using tower-manage
        contacted = ansible_runner.shell('tower-manage uses_mongo')
        result = contacted.values()[0]

        assert 'MongoDB NOT required' in result['stdout'], \
            "Unexpected stdout when checking that MongoDB is inactive using tower-manage - %s." % result['stdout']

        # check using ansible-tower-service
        contacted = ansible_runner.command("ansible-tower-service status")
        result = contacted.values()[0]

        # FIXME: use regex here
        assert 'mongodb' not in result['stdout'], \
            "Unexpected stdout when checking that MongoDB is inactive using ansible-tower-service - %s." % result['stdout']


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Upgrade_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_basic_license')

    def test_upgrade_from_basic_to_enteprise(self, enterprise_license_json, api_config_pg, ansible_runner, tower_license_path):
        '''That a basic license can get upgraded to an enterprise license by posting to api_config_pg.'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(enterprise_license_json)

        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']

        # Assert that /etc/tower/license was modified
        assert before_md5 != after_md5, "The license file was not modified as expected"

    def test_metadata(self, api_config_pg):
        '''Tests that api/v1/config reflects the new enterprise license.'''
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

    def test_mongodb_activated(self, ansible_runner):
        '''Tests that MongoDB is activated.'''
        # check using tower-manage
        contacted = ansible_runner.shell('tower-manage uses_mongo')
        result = contacted.values()[0]

        assert 'MongoDB required' in result['stdout'], \
            "Unexpected stdout when checking that MongoDB is active using tower-manage - %s." % result['stdout']

        # check using ansible-tower-service
        contacted = ansible_runner.command("ansible-tower-service status")
        result = contacted.values()[0]

        # FIXME: use regular expressions here
        assert 'mongod' in result['stdout'], \
            "Unexpected stdout when checking that MongoDB is active using ansible-tower-service - %s." % result['stdout']
