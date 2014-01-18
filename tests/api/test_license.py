'''
 == Demo Tests ==
 1. Ensure instance counts are correct
 2. Add systems and verify counts adjust
 3. Manually add a system to exceed demo instance max
 4. Import inventory that would exceed instance_max
 5. Disable existing hosts and verify instance counts

 == Demo Tests ==
 1. Verify a valid license has no warning or expired
 2. Verify a valid license has expected system counts
 3. Add systems and verify instance_counts
 4. Exceed instance_max manually and via inventory sync
 5. Disable existing hosts and verify instance counts
 6. Test upgrading license ... does it increase instance_count?
 7. Test date_warning=False, date_warning=True, and date_expired=True

'''

import pytest
import jsonschema
import common.tower.license
from tests.api import Base_Api_Test

# The following fixture runs once for this entire module
@pytest.fixture(scope='module')
def backup_license(request, ansible_runner):
    ansible_runner.shell('test -f /etc/awx/aws && mv /etc/awx/aws /etc/awx/.aws', creates='/etc/awx/.aws', removes='/etc/awx/aws')
    ansible_runner.shell('test -f /etc/awx/license && mv /etc/awx/license /etc/awx/.license', creates='/etc/awx/.license', removes='/etc/awx/license')

    def teardown():
        ansible_runner.shell('test -f /etc/awx/.aws && mv /etc/awx/.aws /etc/awx/aws', creates='/etc/awx/aws', removes='/etc/awx/.aws')
        ansible_runner.shell('test -f /etc/awx/.license && mv /etc/awx/.license /etc/awx/license', creates='/etc/awx/license', removes='/etc/awx/.license')
    request.addfinalizer(teardown)

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_demo_license(request, ansible_runner):
    ansible_runner.file(path='/etc/awx/aws', state='absent')
    ansible_runner.file(path='/etc/awx/license', state='absent')

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_license(request, ansible_runner):

    fname = common.tower.license.generate_license_file(instance_count=20, days=31)
    # Using ansible, copy the license to the target system
    ansible_runner.copy(src=fname, dest='/etc/awx/license', owner='awx', group='awx', mode='0600')

    def teardown():
        ansible_runner.file(path='/etc/awx/license', state='absent')
    request.addfinalizer(teardown)

@pytest.fixture(scope='session')
def ami_id(ansible_runner):
    output = ansible_runner.command('/usr/bin/ec2metadata --ami-id')
    return output['stdout']

@pytest.fixture(scope='session')
def instance_id(ansible_runner):
    output = ansible_runner.command('/usr/bin/ec2metadata --instance-id')
    return output['stdout']

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_aws(request, testsetup, ansible_runner, ami_id, instance_id):
    fname = common.tower.license.generate_aws_file(instance_count=20, ami_id=ami_id, instance_id=instance_id)
    ansible_runner.copy(src=fname, dest='/etc/awx/aws', owner='awx', group='awx', mode='0600')

    def teardown():
        ansible_runner.file(path='/etc/awx/aws', state='absent')
    request.addfinalizer(teardown)

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
class Test_Demo_License(Base_Api_Test):
    @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_demo_license')
    def test_metadata(self, api_config_pg):
        conf = api_config_pg.get()

        # Demo mode
        assert 'demo' in conf.license_info
        assert conf.license_info.demo

        # No key installed
        assert 'key_present' in conf.license_info
        assert not conf.license_info.key_present

    # Create inventory and hosts
    @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_demo_license')
    def test_instance_counts(self, api_config_pg):
        conf = api_config_pg.get()

        # Verify number of instances
        assert conf.license_info.current_instances == 0
        assert conf.license_info.free_instances == 10
        assert conf.license_info.available_instances == 10

        # FIXME - start adding hosts

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
# AWS licensing only works when tested on an ec2 instance
@pytest.mark.skipif("'ec2' not in pytest.config.getvalue('base_url')")
class Test_AWS_License(Base_Api_Test):
    @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_aws')
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

    # Create inventory and hosts
    @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_aws')
    def test_instance_counts(self, api_config_pg):
        conf = api_config_pg.get()

        # Verify number of instances
        assert conf.license_info.compliant
        assert conf.license_info.current_instances == 0
        assert conf.license_info.free_instances == \
            conf.license_info.instance_count - conf.license_info.current_instances
        assert conf.license_info.available_instances == conf.license_info.instance_count

        # FIXME - start adding hosts

@pytest.mark.skip_selenium
@pytest.mark.nondestructive
class Test_License(Base_Api_Test):
    @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license')
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
    @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license')
    def test_instance_counts(self, api_config_pg):
        conf = api_config_pg.get()

        # Verify number of instances
        assert conf.license_info.compliant
        assert conf.license_info.current_instances == 0
        assert conf.license_info.free_instances == \
            conf.license_info.instance_count - conf.license_info.current_instances
        assert conf.license_info.available_instances == conf.license_info.instance_count

        # FIXME - start adding hosts
