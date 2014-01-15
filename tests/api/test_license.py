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

# The following fixture runs once for each class that uses it
@pytest.fixture(scope='class')
def install_aws(request, testsetup, ansible_runner):

    fname = common.tower.license.generate_aws_file(instance_count=20)
    # Using ansible, copy the license to the target system
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
class Test_AWS_License(Base_Api_Test):
    @pytest.mark.usefixtures('authtoken', 'backup_license', 'install_aws')
    def test_metadata(self, api_config_pg):

        #     "valid_key": true, 
        #     "license_key": "e8bd586ce98a692e8549a63d070d9ed2db888a0163ad1bc395d70550d2fc7a55", 
        #     "license_date": 9223372036854775807, 

        #     "compliant": true, 
        #     "free_instances": 30, 
        #     "available_instances": 30, 
        #     "current_instances": 0, 
        #     "instance_count": 30, 

        #     "time_remaining": 9223372036854775807, 
        #     "date_expired": false, 
        #     "date_warning": false, 

        #     "is_aws": true, 
        #     "ami-id": "ami-eb81b182", 
        #     "instance-id": "i-fd64c1d3"

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

        # 'valid_key': True,
        # 'license_key': u'768a4aad8cbb49c4762a097f004e0c32783301dfbd20c50edebdbf17cbc42877',
        # 'license_date': 1392497194,

        # 'compliant': True,
        # 'current_instances': 0,
        # 'available_instances': 20,
        # 'free_instances': 20,
        # 'instance_count': 20,

        # 'date_expired': False,
        # 'date_warning': False,
        # 'time_remaining': 2678396,

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
