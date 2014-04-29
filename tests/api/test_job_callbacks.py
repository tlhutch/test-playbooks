import pytest
import uuid
import time
import random
import httplib
import json
import urllib2
import common.tower.license
import common.utils
import common.exceptions
from tests.api import Base_Api_Test

@pytest.fixture(scope="class")
def host_config_key():
    '''Returns a uuid4 string for use as a host_config_key.'''
    return str(uuid.uuid4())

@pytest.fixture(scope="function")
def random_ipv4(request, ansible_facts):
    '''Return a randomly generated ipv4 address.'''
    return ".".join(str(random.randint(1, 255)) for i in range(4))

@pytest.fixture(scope="class")
def ansible_default_ipv4(request, ansible_facts):
    '''Return the ansible_default_ipv4 from ansible_facts of the system under test.'''
    return ansible_facts['ansible_default_ipv4']['address']

@pytest.fixture(scope="function")
def inventory_localhost(request, authtoken, api_hosts_pg, random_group, ansible_default_ipv4):
    '''Create a random inventory host where ansible_ssh_host == ansible_default_ipv4.'''
    payload = dict(name="random_host_alias - %s" % common.utils.random_ascii(),
                   description="host-%s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host=ansible_default_ipv4, ansible_connection="local")),
                   inventory=random_group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=random_group.id))
    return obj

@pytest.fixture(scope="function")
def inventory_127001(request, authtoken, api_hosts_pg, random_group, ansible_default_ipv4):
    '''Create a random inventory host where ansible_ssh_host == ansible_default_ipv4.'''
    payload = dict(name="random_host_alias - %s" % common.utils.random_ascii(),
                   description="host-%s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host=ansible_default_ipv4, ansible_connection="local")),
                   inventory=random_group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=random_group.id))
    return obj

@pytest.fixture(scope="class")
def my_ip(request):
    '''Return the IP address of the system running pytest'''
    return json.load(urllib2.urlopen('http://httpbin.org/ip'))['origin']

@pytest.fixture(scope="function")
def inventory_this_host(request, authtoken, api_hosts_pg, random_group, my_ip):
    '''Create an inventory host matching the public ipv4 address of the system running pytest.'''
    payload = dict(name=my_ip,
                   description="test host %s" % common.utils.random_unicode(),
                   inventory=random_group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=random_group.id))
    return obj

@pytest.fixture(scope="function")
def inventory_this_host_with_alias(request, authtoken, api_hosts_pg, random_group, my_ip, random_ipv4):
    '''Create an inventory host matching the public ipv4 address of the system running pytest, but use a rando'''
    payload = dict(name=my_ip,
                   description="test host %s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host=random_ipv4, ansible_connection="local")),
                   inventory=random_group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=random_group.id))
    return obj

@pytest.fixture(scope="function")
def random_job_template_with_limit(request, authtoken, api_job_templates_pg, random_project, random_inventory, random_ssh_credential, host_config_key):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with limit - %s" % common.utils.random_unicode(),
                   inventory=random_inventory.id,
                   job_type='run',
                   project=random_project.id,
                   limit='No_Match',
                   credential=random_ssh_credential.id,
                   host_config_key=host_config_key,
                   playbook='site.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.fixture(scope="function")
def random_job_template_ask(request, authtoken, api_job_templates_pg, random_project, random_inventory, random_ssh_credential_ask, host_config_key):
    '''Create a job_template with a valid machine credential, but a limit parameter that matches nothing'''
    payload = dict(name="job_template-%s" % common.utils.random_unicode(),
                   description="Random job_template with ASK credential - %s" % common.utils.random_unicode(),
                   inventory=random_inventory.id,
                   job_type='run',
                   project=random_project.id,
                   credential=random_ssh_credential_ask.id,
                   host_config_key=host_config_key,
                   playbook='site.yml', ) # This depends on the project selected
    obj = api_job_templates_pg.post(payload)
    request.addfinalizer(obj.delete)
    return obj

@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Callback(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_1000')

    def test_get(self, api_jobs_pg, ansible_runner, random_job_template, host_config_key, inventory_this_host, inventory_localhost):
        '''Assert a GET on the /callback resource returns a list of matching hosts'''
        # enable callback
        random_job_template.patch(host_config_key=host_config_key)
        assert random_job_template.host_config_key == host_config_key

        # Assert the GET response includes the proper host_config_key
        callback_pg = random_job_template.get_related('callback')
        assert callback_pg.host_config_key == host_config_key

        # Assert the GET response includes expected inventory counts
        all_inventory_hosts = inventory_this_host.get_related('inventory').get_related('hosts')
        assert all_inventory_hosts.count == 2, "Unexpected number of inventory_hosts (%s != 2)" % all_inventory_hosts.count
        assert len(callback_pg.matching_hosts) == 1, "Unexpected number of matching_hosts (%s != 1)" % len(callback_pg.matching_hosts)

        # Assert the GET response includes expected values in matching_hosts
        assert inventory_this_host.name in callback_pg.matching_hosts
        assert inventory_localhost.name not in callback_pg.matching_hosts

    def test_launch_no_hosts(self, api_jobs_pg, ansible_runner, random_job_template, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when no matching inventory host can be found'''
        # enable callback
        random_job_template.patch(host_config_key=host_config_key)
        assert random_job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.BAD_REQUEST, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.BAD_REQUEST, result)
        assert result['failed']
        assert result['json']['msg'] == 'No matching host could be found!'

    def test_launch_no_hosts_match(self, api_jobs_pg, ansible_runner, random_job_template, host_config_key, ansible_default_ipv4, inventory_this_host_with_alias):
        '''Verify launch failure when a matching host.name is found, but ansible_ssh_host is different.'''
        # enable callback
        random_job_template.patch(host_config_key=host_config_key)
        assert random_job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert 'status' in result, "Unxpected response: %s" % result
        assert result['status'] == httplib.BAD_REQUEST, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.BAD_REQUEST, result)
        assert result['failed']
        assert result['json']['msg'] == 'No matching host could be found!'

    def test_launch_badkey(self, api_jobs_pg, ansible_runner, random_job_template, inventory_localhost, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when providing incorrect host_config_key'''
        # enable callback
        random_job_template.patch(host_config_key=host_config_key)
        assert random_job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template.json['related']['callback']),
                    body="host_config_key=BOGUS",)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.FORBIDDEN, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.FORBIDDEN, result)
        assert result['failed']
        assert result['json']['detail'] == 'You do not have permission to perform this action.'

    def test_launch_no_credential(self, api_jobs_pg, ansible_runner, random_job_template_no_credential, inventory_localhost, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when launching a job_template with no credentials'''
        # enable callback
        random_job_template_no_credential.patch(host_config_key=host_config_key)
        assert random_job_template_no_credential.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template_no_credential.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.BAD_REQUEST
        assert result['failed']
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_ask_credential(self, api_jobs_pg, ansible_runner, random_job_template_ask, inventory_localhost, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when launching a job_template with ASK credentials'''
        # assert callback
        assert random_job_template_ask.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template_ask.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.BAD_REQUEST
        assert result['failed']
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_multiple_hosts(self, api_jobs_pg, ansible_runner, random_job_template, inventory_localhost, inventory_127001, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when launching a job_template where multiple hosts match '''

        # enable callback
        random_job_template.patch(host_config_key=host_config_key)
        assert random_job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.BAD_REQUEST
        assert 'failed' in result and result['failed']
        assert result['json']['msg'] == 'Multiple hosts matched the request!'

    def test_launch_success_limit(self, api_jobs_pg, ansible_runner, random_job_template_with_limit, inventory_localhost, host_config_key, ansible_default_ipv4):
        '''Assert that launching a callback job against a job_template with an existing 'limit' parameter successfully launches, but the job fails because no matching hosts were found.'''

        assert random_job_template_with_limit.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template_with_limit.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.ACCEPTED
        assert not result['changed']
        assert 'failed' not in result, "Callback failed\n%s" % result
        assert result['content_length'].isdigit() and int(result['content_length']) == 0

        # FIXME - assert 'Location' header points to launched job
        # https://github.com/ansible/ansible-commander/commit/05febca0857aa9c6575a193072918949b0c1227b

        # Wait for job to complete
        jobs_pg = random_job_template_with_limit.get_related('jobs', launch_type='callback', order_by='-id')
        assert jobs_pg.count == 1
        job_pg = jobs_pg.results[0].wait_until_completed(timeout=5*60)

        assert job_pg.launch_type == "callback"

        # Assert job failed because no hosts were found
        assert job_pg.status == "failed"
        assert "ERROR: provided hosts list is empty" in job_pg.result_stdout

    def test_launch_success(self, api_jobs_pg, ansible_runner, random_job_template, inventory_localhost, host_config_key, ansible_default_ipv4):
        '''Assert that launching a callback job against a job_template with an existing 'limit' parameter successfully launches, and the job successfully runs on a single host..'''

        # enable callback
        random_job_template.patch(host_config_key=host_config_key)
        assert random_job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, random_job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.ACCEPTED
        assert not result['changed']
        assert 'failed' not in result, "Callback failed\n%s" % result
        assert result['content_length'].isdigit() and int(result['content_length']) == 0

        # FIXME - assert 'Location' header points to launched job
        # https://github.com/ansible/ansible-commander/commit/05febca0857aa9c6575a193072918949b0c1227b

        # Wait for job to complete
        jobs_pg = random_job_template.get_related('jobs', launch_type='callback', order_by='-id')
        assert jobs_pg.count == 1
        job_pg = jobs_pg.results[0].wait_until_completed(timeout=5*60)

        assert job_pg.launch_type == "callback"

        # Make sure there is no traceback in result_stdout or result_traceback
        assert job_pg.is_successful, \
            "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s\nJob explanation: %s" % \
            (job_pg.status, job_pg.result_stdout, job_pg.result_traceback, job_pg.job_explanation)

        # Assert only a single host was affected
        host_summaries_pg = job_pg.get_related('job_host_summaries')
        assert host_summaries_pg.count == 1

        # Assert the expected host matches
        assert host_summaries_pg.results[0].host == inventory_localhost.id
