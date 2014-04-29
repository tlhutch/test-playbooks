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
import jsonschema
import common.utils
import common.tower.license
import common.exceptions
from tests.api import Base_Api_Test

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_demo_license(request, backup_license, ansible_runner):
    ansible_runner.file(path='/etc/awx/aws', state='absent')
    ansible_runner.file(path='/etc/awx/license', state='absent')

@pytest.fixture(scope='class')
def license_instance_count(request, ansible_runner):
    '''Number of host instances permitted by the license'''
    return 20

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_license(request, ansible_runner, license_instance_count, backup_license):
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=31)
    # Using ansible, copy the license to the target system
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_license_warning(request, ansible_runner, license_instance_count, backup_license):
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=1)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')
    def teardown():
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_license_expired(request, ansible_runner, license_instance_count, backup_license):
    fname = common.tower.license.generate_license_file(instance_count=license_instance_count, days=-1)
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')
    def teardown():
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)

@pytest.fixture(scope='class')
def ansible_ec2_facts(ansible_runner):
    '''This will only work on an ec2 system'''
    return ansible_runner.ec2_facts()

@pytest.fixture(scope='class')
def ami_id(ansible_ec2_facts):
    return ansible_ec2_facts['ansible_ec2_ami_id']

@pytest.fixture(scope='class')
def instance_id(ansible_ec2_facts):
    return ansible_ec2_facts['ansible_ec2_instance_id']

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_aws(request, ansible_runner, license_instance_count, ami_id, instance_id, backup_license):
    fname = common.tower.license.generate_aws_file(instance_count=license_instance_count, ami_id=ami_id, instance_id=instance_id)
    ansible_runner.copy(src=fname, dest='/etc/awx/aws', owner='awx', group='awx', mode='0600')

    def teardown():
        ansible_runner.file(path='/etc/awx/aws', state='absent')
    request.addfinalizer(teardown)

@pytest.fixture(scope="class")
def organization(request, authtoken, api_organizations_pg):
    payload = dict(name="org-%s" % common.utils.random_unicode())
    obj = api_organizations_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def inventory(request, authtoken, api_inventories_pg, api_groups_pg, api_hosts_pg, organization):
    payload = dict(name="inventory-%s" % common.utils.random_unicode(),
                   organization=organization.id,
                   variables=json.dumps(dict(ansible_connection='local')))
    obj = api_inventories_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="class")
def group(request, authtoken, api_groups_pg, inventory):
    payload = dict(name="group-%s" % common.utils.random_unicode(),
                   inventory=inventory.id,
                   variables=json.dumps(dict(ansible_connection='local')))
    obj = api_groups_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

class Base_License_Test(Base_Api_Test):
    '''Base class for sharing test_instance_count method'''

    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):

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
                (conf.license_info.current_instances, conf.license_info.free_instances, \
                 conf.license_info.available_instances )

            # Add a host to the inventory group
            payload = dict(name="host-%s" % common.utils.random_ascii(),
                           description="host-%s" % common.utils.random_unicode(),
                           inventory=group.inventory)
            # The first 20 hosts should succeed
            if current_hosts < license_instance_count:
                group_hosts_pg.post(payload)
                current_hosts += 1
            # Anything more than 'license_instance_count' will raise a 403
            else:
                with pytest.raises(common.exceptions.LicenseExceeded_Exception):
                    result = group_hosts_pg.post(payload)
                break

        # Verify maximum instances
        assert current_hosts == license_instance_count
        assert conf.license_info.current_instances == license_instance_count
        assert conf.license_info.free_instances == 0
        assert conf.license_info.available_instances == license_instance_count

@pytest.mark.skip_selenium
class Test_Demo_License(Base_License_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_demo_license')

    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()

        # Demo mode
        assert 'demo' in conf.license_info
        assert conf.license_info.demo

        # No key installed
        assert 'key_present' in conf.license_info
        assert not conf.license_info.key_present

    def test_instance_counts(self, api_config_pg, inventory, group):
        super(Test_Demo_License, self).test_instance_counts(api_config_pg, 10, inventory, group)

@pytest.mark.skip_selenium
class Test_AWS_License(Base_License_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_aws')

    # AWS licensing only works when tested on an ec2 instance
    @pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
    def test_metadata(self, api_config_pg):

        conf = api_config_pg.get()

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
        super(Test_AWS_License, self).test_instance_counts(api_config_pg, license_instance_count, inventory, group)

@pytest.mark.skip_selenium
class Test_License(Base_License_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license')

    def test_metadata(self, api_config_pg):

        conf = api_config_pg.get()

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

    # Create inventory and hosts
    def test_instance_counts(self, api_config_pg, license_instance_count, inventory, group):
        super(Test_License, self).test_instance_counts(api_config_pg, license_instance_count, inventory, group)

@pytest.mark.skip_selenium
class Test_License_Warning(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_warning')

    def test_metadata(self, api_config_pg):

        conf = api_config_pg.get()

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

@pytest.mark.skip_selenium
class Test_License_Expired(Base_Api_Test):
    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_expired')

    def test_metadata(self, api_config_pg):

        conf = api_config_pg.get()

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
