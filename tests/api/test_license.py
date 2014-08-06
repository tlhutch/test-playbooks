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
def license_instance_count(request, ansible_runner):
    '''Number of host instances permitted by the license'''
    return 20


@pytest.fixture(scope='class')
def install_trial_license(request, ansible_runner, license_instance_count):
    log.debug("calling fixture install_trial_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31, trial=True)
    # Using ansible, copy the license to the target system
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')


@pytest.fixture(scope='class')
def install_license(request, ansible_runner, license_instance_count):
    log.debug("calling fixture install_license")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31)
    # Using ansible, copy the license to the target system
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')


@pytest.fixture(scope='class')
def install_license_warning(request, ansible_runner, license_instance_count):
    log.debug("calling fixture install_license_warning")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=1)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')


@pytest.fixture(scope='class')
def install_license_expired(request, ansible_runner, license_instance_count):
    log.debug("calling fixture install_license_expired")
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=-1)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')


@pytest.fixture(scope='class')
def ansible_ec2_facts(ansible_runner):
    '''This will only work on an ec2 system'''
    return ansible_runner.ec2_facts().get('ansible_facts', {})


@pytest.fixture(scope='class')
def ami_id(ansible_ec2_facts):
    return ansible_ec2_facts['ansible_ec2_ami_id']


@pytest.fixture(scope='class')
def instance_id(ansible_ec2_facts):
    return ansible_ec2_facts['ansible_ec2_instance_id']


@pytest.fixture(scope='class')
def install_license_aws(request, ansible_runner, license_instance_count, ami_id, instance_id):
    log.debug("calling fixture install_license_aws")
    fname = common.tower.license.generate_aws_file(instance_count=license_instance_count, ami_id=ami_id, instance_id=instance_id)
    ansible_runner.copy(src=fname, dest='/etc/awx/aws', owner='awx', group='awx', mode='0600')


@pytest.fixture(scope="function", params=['org_admin', 'org_user', 'anonymous'])
def non_admin_user(request, org_admin, org_user, anonymous_user):
    if request.param == 'org_admin':
        return org_admin
    elif request.param == 'org_user':
        return org_user
    elif request.param == 'anonymous':
        return anonymous_user
    else:
        raise Exception("Unhandled fixture parameter: %s" % request.param)


def assert_instance_counts(api_config_pg, license_instance_count, inventory, group):
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
        payload = dict(name="host-%s" % common.utils.random_ascii(),
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


@pytest.mark.skip_selenium
class Test_No_License(Base_Api_Test):
    '''
    Verify /config behaves as expected when no license is installed
    '''
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license')

    def test_metadata(self, api_config_pg):
        '''Verify the license_info field is empty'''
        conf = api_config_pg.get()
        assert conf.license_info == {}, "Expecting empty license_info, found: %s" % json.dumps(conf.license_info, indent=4)

    def test_host(self, inventory, group):
        '''Verify that no hosts can be added'''
        payload = dict(name="host-%s" % common.utils.random_unicode(),
                       description="host-%s" % common.utils.random_unicode(),
                       inventory=group.inventory)
        group_hosts_pg = group.get_related('hosts')
        with pytest.raises(common.exceptions.Forbidden_Exception):
            group_hosts_pg.post(payload)

    def test_job_launch(self, job_template):
        '''Verify that job_templates cannot be launched'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()


@pytest.mark.skip_selenium
class Test_AWS_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_aws')

    # AWS licensing only works when tested on an ec2 instance
    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.license_info)

        # Assert NOT Demo mode
        assert 'demo' not in conf.license_info
        assert 'key_present' not in conf.license_info

        # Assert a valid key
        assert conf.license_info.valid_key
        assert 'license_key' in conf.license_info

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert not conf.license_info.date_warning

        # AWS info
        assert conf.license_info.is_aws
        assert 'ami-id' in conf.license_info
        assert 'instance-id' in conf.license_info
        assert 'instance_count' in conf.license_info

    # AWS licensing only works when tested on an ec2 instance
    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        assert_instance_counts(api_config_pg, license_instance_count, inventory, group)

    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_info' in conf.json
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_info' in conf.json
            assert 'license_key' not in conf.license_info


@pytest.mark.skip_selenium
class Test_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license')

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)

        # Assert NOT Demo mode
        assert 'demo' not in conf.license_info
        assert 'key_present' not in conf.license_info

        # Assert a valid key
        assert conf.license_info.valid_key
        assert 'license_key' in conf.license_info
        assert 'instance_count' in conf.license_info

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert not conf.license_info.date_warning

        # Assert not AWS information
        assert 'is_aws' not in conf.license_info
        assert 'ami-id' not in conf.license_info
        assert 'instance-id' not in conf.license_info

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000

    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        assert_instance_counts(api_config_pg, license_instance_count, inventory, group)

    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_info' in conf.json
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_info' in conf.json
            assert 'license_key' not in conf.license_info


@pytest.mark.skip_selenium
class Test_License_Warning(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_warning')

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)

        # Assert NOT Demo mode
        assert 'demo' not in conf.license_info
        assert 'key_present' not in conf.license_info

        # Assert a valid key
        assert conf.license_info.valid_key
        assert 'license_key' in conf.license_info
        assert 'instance_count' in conf.license_info

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert conf.license_info.date_warning

        # Assert not AWS information
        assert 'is_aws' not in conf.license_info
        assert 'ami-id' not in conf.license_info
        assert 'instance-id' not in conf.license_info

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000


@pytest.mark.skip_selenium
class Test_License_Expired(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_expired')

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)

        # Assert NOT Demo mode
        assert 'demo' not in conf.license_info
        assert 'key_present' not in conf.license_info

        # Assert a valid key
        assert conf.license_info.valid_key
        assert 'license_key' in conf.license_info
        assert 'instance_count' in conf.license_info

        # Assert dates look sane?
        assert conf.license_info.date_expired
        assert conf.license_info.date_warning

        # Assert not AWS information
        assert 'is_aws' not in conf.license_info
        assert 'ami-id' not in conf.license_info
        assert 'instance-id' not in conf.license_info

        # Assert grace_period is 30 days + time_remaining
        assert int(conf.license_info['grace_period_remaining']) == \
            int(conf.license_info['time_remaining']) + 2592000

    def test_job_launch(self, job_template):
        '''Verify that job_templates cannot be launched'''
        with pytest.raises(common.exceptions.Forbidden_Exception):
            job_template.launch_job()


@pytest.mark.skip_selenium
class Test_Trial_License(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_trial_license')

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)

        # Assert NOT Demo mode
        assert 'demo' not in conf.license_info
        assert 'key_present' not in conf.license_info

        # Assert a valid key
        assert conf.license_info.valid_key
        assert 'license_key' in conf.license_info
        assert 'instance_count' in conf.license_info

        # Assert dates look sane?
        assert not conf.license_info.date_expired
        assert not conf.license_info.date_warning

        # Assert not AWS information
        assert 'is_aws' not in conf.license_info
        assert 'ami-id' not in conf.license_info
        assert 'instance-id' not in conf.license_info

        # Assert there is no grace_period, it should match time_remaining
        assert conf.license_info['grace_period_remaining'] == conf.license_info['time_remaining']

    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        assert_instance_counts(api_config_pg, license_instance_count, inventory, group)

    def test_key_visibility_admin(self, api_config_pg):
        conf = api_config_pg.get()
        print json.dumps(conf.json, indent=4)
        assert 'license_info' in conf.json
        assert 'license_key' in conf.license_info

    def test_key_visibility_non_admin(self, api_config_pg, non_admin_user, user_password):
        with self.current_user(non_admin_user.username, user_password):
            conf = api_config_pg.get()
            print json.dumps(conf.json, indent=4)
            assert 'license_info' in conf.json
            assert 'license_key' not in conf.license_info
