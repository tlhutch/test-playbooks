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

import json
import pytest
import logging
import common.utils
import common.tower.license
import common.exceptions
from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope='class')
def license_instance_count(request):
    '''Number of host instances permitted by the license'''
    return 20


@pytest.fixture(scope='class')
def install_trial_license(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_trial_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31, trial=True)
    # Using ansible, copy the license to the target system
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='function')
def license_json(request, license_instance_count):
    return common.tower.license.generate_license(instance_count=license_instance_count,
                                                 days=31,
                                                 company_name=common.utils.random_unicode(),
                                                 contact_name=common.utils.random_unicode(),
                                                 contact_email="%s@example.com" % common.utils.random_unicode())


@pytest.fixture(
    scope="function",
    params=[None, 0, 1, -1, True, common.utils.random_unicode(), (), {}, {'eula_accepted': True}],
)
def invalid_license_json(request):
    return request.param


@pytest.fixture(scope='function')
def missing_eula_license_json(request, license_json):
    del license_json['eula_accepted']
    return license_json


@pytest.fixture(scope='function')
def eula_rejected_license_json(request, license_json):
    license_json['eula_accepted'] = False
    return license_json


@pytest.fixture(scope='function')
def trial_license_json(request, license_instance_count):
    return common.tower.license.generate_license(instance_count=license_instance_count,
                                                 days=31,
                                                 trial=True,
                                                 company_name=common.utils.random_unicode(),
                                                 contact_name=common.utils.random_unicode(),
                                                 contact_email="%s@example.com" % common.utils.random_unicode())


@pytest.fixture(scope='class')
def install_license(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31)
    # Using ansible, copy the license to the target system
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_license_warning(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_license_warning")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=1)
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_license_expired(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_license_expired")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=-61)
    contacted = ansible_runner.copy(src=fname, dest=tower_license_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope='class')
def install_license_grace_period(request, ansible_runner, license_instance_count, tower_license_path):
    log.debug("calling fixture install_license_grace_period")
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
def install_license_aws(request, ansible_runner, license_instance_count, ami_id, instance_id, tower_aws_path):
    log.debug("calling fixture install_license_aws")
    fname = common.tower.license.generate_aws_file(instance_count=license_instance_count, ami_id=ami_id, instance_id=instance_id)
    contacted = ansible_runner.copy(src=fname, dest=tower_aws_path, owner='awx', group='awx', mode='0600')
    for result in contacted.values():
        assert 'failed' not in result, "Failure installing license\n%s" % json.dumps(result, indent=2)


@pytest.fixture(scope="function", params=['org_admin', 'org_user', 'anonymous_user'])
def non_admin_user(request):
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def inventory_no_free_instances(request, authtoken, api_config_pg, api_inventories_pg, organization):
    payload = dict(name="inventory-%s" % common.utils.random_ascii(),
                   description="Random inventory - %s" % common.utils.random_unicode(),
                   organization=organization.id,)
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)

    # Ensure there are at least 5 active hosts
    hosts_pg = obj.get_related('hosts')
    while api_config_pg.get().license_info.instance_count < 5:
        payload = dict(name="host-%s" % common.utils.random_unicode().replace(':', ''),
                       inventory=obj.id)
        hosts_pg.post(payload)

    # Install a license with instance_count=3
    json = common.tower.license.generate_license(instance_count=3,
                                                 days=-1,
                                                 trial=False,
                                                 company_name=common.utils.random_unicode(),
                                                 contact_name=common.utils.random_unicode(),
                                                 contact_email="%s@example.com" % common.utils.random_unicode())
    api_config_pg.post(json)

    return obj


def assert_instance_counts(api_config_pg, license_instance_count, group):
    '''Verify hosts can be added up to the provided 'license_instance_count' variable'''

    # Get API resource /groups/N/hosts
    group_hosts_pg = group.get_related('hosts')

    current_hosts = 0
    while current_hosts <= license_instance_count + 1:
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
        payload = dict(name="host-%s" % common.utils.random_unicode().replace(':', ''),
                       description="host-%s" % common.utils.random_unicode(),
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
        payload = dict(name="host-%s" % common.utils.random_unicode().replace(':', ''),
                       description="host-%s" % common.utils.random_unicode(),
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

    def test_post_license_without_eula_accepted(self, api_config_pg, missing_eula_license_json):
        '''Verify failure while POSTing a license with no `eula_accepted` attribute.'''

        with pytest.raises(common.exceptions.LicenseInvalid_Exception):
            api_config_pg.post(missing_eula_license_json)

    def test_post_license_with_rejected_eula(self, api_config_pg, eula_rejected_license_json):
        '''Verify failure while POSTing a license with `eula_accepted:false` attribute.'''

        with pytest.raises(common.exceptions.LicenseInvalid_Exception):
            api_config_pg.post(eula_rejected_license_json)

    def test_post_license(self, api_config_pg, license_json, ansible_runner, tower_license_path):
        '''Verify that a license can be installed by issuing a POST to the /config endpoint'''
        # Assert that /etc/tower/license does not exist
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert not result['stat']['exists'], "No license was expected, but one was found"

        # Install the license
        api_config_pg.post(license_json)

        # Assert that /etc/tower/license was created
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            assert result['stat']['exists'], "A license was not succesfully installed to %s" % (tower_license_path)


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_AWS_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_aws')

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

    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        '''Verify that hosts can be added up to the 'license_instance_count' '''
        if api_config_pg.get().license_info['current_instances'] > 0:
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
    def test_update_license(self, api_config_pg, license_json, ansible_runner, tower_license_path, tower_aws_path):
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
        api_config_pg.post(license_json)

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
class Test_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license')

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


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_License_Warning(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_warning')

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

    def test_update_license(self, api_config_pg, license_json, ansible_runner, tower_license_path):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(license_json)

        # Assert that /etc/tower/license was modified
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']
        assert before_md5 != after_md5, "The license file was not modified as expected"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_License_Grace_Period(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_grace_period')

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
class Test_License_Expired(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_expired')

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

    def test_host(self, inventory, group):
        '''Verify that no hosts can be added'''
        payload = dict(name="host-%s" % common.utils.random_unicode().replace(':', ''),
                       description="host-%s" % common.utils.random_unicode(),
                       inventory=group.inventory)
        group_hosts_pg = group.get_related('hosts')
        with pytest.raises(common.exceptions.Forbidden_Exception):
            group_hosts_pg.post(payload)

    def test_job_launch(self, job_template):
        '''Verify that job_templates cannot be launched'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()

    def test_update_license(self, api_config_pg, license_json, ansible_runner, tower_license_path):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(license_json)

        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']

        # Assert that /etc/tower/license was modified
        assert before_md5 != after_md5, "The license file was not modified as expected"


@pytest.mark.api
@pytest.mark.skip_selenium
class Test_Trial_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_trial_license')

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

    def test_update_license(self, api_config_pg, trial_license_json, ansible_runner, tower_license_path):
        '''Verify that the license can be updated by issuing a POST to the /config endpoint'''
        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            before_md5 = result['stat']['md5']

        # Update the license
        api_config_pg.post(trial_license_json)

        # Record the license md5
        contacted = ansible_runner.stat(path=tower_license_path)
        for result in contacted.values():
            after_md5 = result['stat']['md5']

        # Assert that /etc/tower/license was modified
        assert before_md5 != after_md5, "The license file was not modified as expected"
