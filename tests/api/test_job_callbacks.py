import re
import pytest
import httplib
import json
import fauxfactory
import common.exceptions
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def another_host_with_default_ipv4_in_variables(request, authtoken, api_hosts_pg, host_with_default_ipv4_in_variables):
    '''Create a another host object matching host_with_default_ipv4_in_variables'''
    payload = host_with_default_ipv4_in_variables.json
    payload.update(name="another_host_with_default_ipv4_in_variables - %s" % fauxfactory.gen_alphanumeric(),)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group(s)
    for group in host_with_default_ipv4_in_variables.get_related('groups').results:
        with pytest.raises(common.exceptions.NoContent_Exception):
            obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def hosts_with_name_matching_local_ipv4_addresses_but_random_ssh_host(request, group, local_ipv4_addresses):
    '''Create an inventory host matching the public ipv4 address of the system running pytest.'''
    for ipv4_addr in local_ipv4_addresses:
        payload = dict(name=ipv4_addr,
                       description="test host %s" % fauxfactory.gen_utf8(),
                       inventory=group.inventory,
                       variables=json.dumps(dict(ansible_ssh_host=common.utils.random_ipv4(),
                                                 ansible_connection="local")),)
        obj = group.get_related('hosts').post(payload)
        request.addfinalizer(obj.delete)
        # Add to group
        with pytest.raises(common.exceptions.NoContent_Exception):
            obj.get_related('groups').post(dict(id=group.id))

    return group.get_related('hosts', name__in=','.join(local_ipv4_addresses))


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_Callback(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_license_1000')

    def test_get_without_matching_hosts(self, job_template, host_config_key):
        '''Assert a GET on the /callback resource returns an empty list of matching hosts'''
        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # Assert the GET response includes the proper host_config_key
        callback_pg = job_template.get_related('callback')
        assert callback_pg.host_config_key == host_config_key

        # Assert the GET response includes expected inventory counts
        assert len(callback_pg.matching_hosts) == 0, \
            "Unexpected number of matching_hosts (%s != 0)" % len(callback_pg.matching_hosts)

    def test_get_with_matching_hosts(self, ansible_runner, job_template, host_config_key, host_with_default_ipv4_in_variables,
                                     ansible_default_ipv4, testsetup):
        '''Assert a GET on the /callback resource returns a list of matching hosts'''
        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # Assert the GET response includes the proper host_config_key
        callback_pg = job_template.get_related('callback')
        assert callback_pg.host_config_key == host_config_key

        # issue a GET to the callback page from the Tower host
        args = dict(method="GET",
                    status_code=httplib.OK,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    user=testsetup.credentials['users']['admin']['username'],
                    password=testsetup.credentials['users']['admin']['password'],
                    force_basic_auth=True)
        contacted = ansible_runner.uri(**args)

        # verify response
        for result in contacted.values():
            assert result['status'] == httplib.OK
            assert not result['changed']
            assert 'failed' not in result, "GET to callback_pg failed\n%s" % result

        # Assert the GET response includes expected inventory counts
        all_inventory_hosts = host_with_default_ipv4_in_variables.get_related('inventory').get_related('hosts')
        assert all_inventory_hosts.count > 1, "Unexpected number of inventory_hosts (%s <= 1)" % all_inventory_hosts.count
        matching_hosts = contacted.values()[0]['json']['matching_hosts']
        assert len(matching_hosts) == 1, "Unexpected number of matching_hosts (%s != 1)" % len(matching_hosts)

        # Assert the GET response includes expected value in matching_hosts
        assert matching_hosts[0] == host_with_default_ipv4_in_variables.name, \
            "Unexpected matching host displayed on callback_pg - %s." % matching_hosts[0]

    def test_launch_without_hosts(self, ansible_runner, job_template, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when no matching inventory host can be found'''
        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # trigger callback
        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.BAD_REQUEST, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.BAD_REQUEST, result)
            assert result['failed']
            assert result['json']['msg'] == 'No matching host could be found!'

    def test_launch_without_matching_hosts(self, ansible_runner, job_template,
                                           host_config_key, ansible_default_ipv4,
                                           hosts_with_name_matching_local_ipv4_addresses_but_random_ssh_host):
        '''Verify launch failure when a matching host.name is found, but ansible_ssh_host is different.'''
        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert 'status' in result, "Unxpected response: %s" % result
            assert result['status'] == httplib.BAD_REQUEST, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.BAD_REQUEST, result)
            assert result['failed']
            assert result['json']['msg'] == 'No matching host could be found!'

    def test_launch_multiple_host_matches(self, ansible_runner, job_template,
                                          host_with_default_ipv4_in_variables,
                                          another_host_with_default_ipv4_in_variables, host_config_key,
                                          ansible_default_ipv4):
        '''Verify launch failure when launching a job_template where multiple hosts match '''

        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.BAD_REQUEST
            assert 'failed' in result and result['failed']
            assert result['json']['msg'] == 'Multiple hosts matched the request!'

    def test_launch_with_incorrect_hostkey(self, ansible_runner, job_template, host_with_default_ipv4_in_variables, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when providing incorrect host_config_key'''
        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # trigger callback
        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=BOGUS",)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.FORBIDDEN, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.FORBIDDEN, result)
            assert result['failed']
            assert result['json']['detail'] == 'You do not have permission to perform this action.'

    def test_launch_without_credential(self, ansible_runner, job_template_no_credential,
                                       host_with_default_ipv4_in_variables,
                                       host_config_key, ansible_default_ipv4):
        '''Verify launch failure when launching a job_template with no credentials'''
        # enable callback
        job_template_no_credential.patch(host_config_key=host_config_key)
        assert job_template_no_credential.host_config_key == host_config_key

        # trigger callback
        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template_no_credential.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.BAD_REQUEST
            assert result['failed']
            assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_with_ask_credential(self, ansible_runner, job_template_ask, host_with_default_ipv4_in_variables, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when launching a job_template with ASK credentials'''
        # assert callback
        job_template_ask.patch(host_config_key=host_config_key)
        assert job_template_ask.host_config_key == host_config_key

        # trigger callback
        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template_ask.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.BAD_REQUEST
            assert result['failed']
            assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_with_variables_needed_to_start(
        self, ansible_runner, job_template_variables_needed_to_start,
        host_with_default_ipv4_in_variables, host_config_key, ansible_default_ipv4
    ):
        '''Verify launch failure when launching a job_template that has required survey variables.'''
        # assert callback
        job_template_variables_needed_to_start.patch(host_config_key=host_config_key)
        assert job_template_variables_needed_to_start.host_config_key == host_config_key

        # trigger callback
        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template_variables_needed_to_start.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.BAD_REQUEST
            assert result['failed']
            assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_with_limit(self, api_jobs_url, ansible_runner, job_template_with_limit,
                               host_with_default_ipv4_in_variables, host_config_key,
                               ansible_default_ipv4):
        '''
        Assert that launching a callback job against a job_template with an
        existing 'limit' parameter successfully launches, but the job fails
        because no matching hosts were found.
        '''

        # validate host_config_key
        job_template_with_limit.patch(host_config_key=host_config_key)
        assert job_template_with_limit.host_config_key == host_config_key

        # issue callback
        args = dict(method="POST",
                    timeout=60,
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template_with_limit.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.ACCEPTED
            assert not result['changed']
            assert 'failed' not in result, "Callback failed\n%s" % result
            assert result['content_length'].isdigit() and int(result['content_length']) == 0

        # FIXME - assert 'Location' header points to launched job
        # https://github.com/ansible/ansible-commander/commit/05febca0857aa9c6575a193072918949b0c1227b

        # Wait for job to complete
        jobs_pg = job_template_with_limit.get_related('jobs', launch_type='callback', order_by='-id')
        assert jobs_pg.count == 1
        job_pg = jobs_pg.results[0].wait_until_completed(timeout=5 * 60)

        # Assert job failed because no hosts were found
        assert job_pg.launch_type == "callback"
        assert job_pg.status == "failed"

        # Assert expected output in result_stdout
        error_strings = ["Specified --limit does not match any hosts",
                         "provided hosts list is empty"]
        assert any([True for errstr in error_strings if errstr in job_pg.result_stdout]), \
            "Unable to find expected error (%s) in job_pg.result_stdout (%s)" % \
            (error_strings, job_pg.result_stdout)

    def test_launch(self, ansible_runner, job_template, host_with_default_ipv4_in_variables, host_config_key, ansible_default_ipv4):
        '''Assert that launching a callback job against a job_template successfully launches, and the job successfully runs on a single host.'''

        # enable host_config_key
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # issue callback
        args = dict(method="POST",
                    timeout=60,
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # verify callback response
        for result in contacted.values():
            assert result['status'] == httplib.ACCEPTED
            assert not result['changed']
            assert 'failed' not in result, "Callback failed\n%s" % result
            assert result['content_length'].isdigit() and int(result['content_length']) == 0

        # FIXME - assert 'Location' header points to launched job
        # https://github.com/ansible/ansible-commander/commit/05febca0857aa9c6575a193072918949b0c1227b

        # Wait for job to complete
        jobs_pg = job_template.get_related('jobs', launch_type='callback', order_by='-id')
        assert jobs_pg.count == 1
        job_pg = jobs_pg.results[0].wait_until_completed(timeout=5 * 60)

        # Assert job was successful
        assert job_pg.launch_type == "callback"
        assert job_pg.is_successful, \
            "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s\nJob explanation: %s" % \
            (job_pg.status, job_pg.result_stdout, job_pg.result_traceback, job_pg.job_explanation)

        # Assert only a single host was affected
        # NOTE: may need to poll as the job_host_summaries are calculated
        # asynchronously when a job completes.
        host_summaries_pg = job_pg.get_related('job_host_summaries')
        assert host_summaries_pg.count == 1

        # Assert the affected host matches expected
        assert host_summaries_pg.results[0].host == host_with_default_ipv4_in_variables.id

    def test_launch_multiple(self, api_jobs_url, ansible_runner, job_template, host_with_default_ipv4_in_variables, host_config_key, ansible_default_ipv4):
        '''
        Verify that issuing a callback, while a callback job from the same host
        is already running, fails.
        '''

        # enable host_config_key
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # issue multiple callbacks, only the first should succeed
        for attempt in range(3):
            callback_url = "http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback'])
            args = dict(method="POST",
                        timeout=60,
                        status_code=httplib.ACCEPTED,
                        url=callback_url,
                        body="host_config_key=%s" % host_config_key,)
            args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
            contacted = ansible_runner.uri(**args)

            # assert callback response
            for result in contacted.values():
                if attempt == 0:
                    assert result['status'] == httplib.ACCEPTED
                    assert not result['changed']
                    assert 'failed' not in result, "First provisioning callback unexpectedly failed."
                    assert result['content_length'].isdigit() and int(result['content_length']) == 0
                    assert 'location' in result, "Missing expected 'location' in callback response."
                    assert re.search(r'%s[0-9]+/$' % api_jobs_url, result['location']), \
                        "Unexpected format for 'location' header (%s)" % result['location']
                else:
                    assert result['status'] == httplib.BAD_REQUEST
                    assert 'failed' in result, "Subsequent provisioning callback unexpectedly passed."

        # FIXME - assert 'Location' header points to launched job
        # https://github.com/ansible/ansible-commander/commit/05febca0857aa9c6575a193072918949b0c1227b

        # Find all jobs with launch_type=callback
        jobs_pg = job_template.get_related('jobs', launch_type='callback', order_by='-id')

        # Assert only one job found
        assert jobs_pg.count == 1

        # Wait for job to complete
        job_pg = jobs_pg.results[0].wait_until_completed(timeout=60 * 2)

        # Assert job was successful
        assert job_pg.launch_type == "callback"
        assert job_pg.is_successful, \
            "Job unsuccessful (%s)\nJob result_stdout: %s\nJob result_traceback: %s\nJob explanation: %s" % \
            (job_pg.status, job_pg.result_stdout, job_pg.result_traceback, job_pg.job_explanation)

        # Assert only a single host was affected
        host_summaries_pg = job_pg.get_related('job_host_summaries')
        assert host_summaries_pg.count == 1

        # Assert the affected host matches expected
        assert host_summaries_pg.results[0].host == host_with_default_ipv4_in_variables.id

    def test_launch_with_inventory_update(
        self, api_jobs_url, ansible_runner, job_template, host_config_key,
        cloud_group, ansible_default_ipv4, tower_version_cmp
    ):
        '''Assert that a callback job against a job_template also initiates an inventory_update (when configured).'''

        if tower_version_cmp('2.0.0') < 0:
            pytest.xfail("Only supported on tower-2.0.0 (or newer)")

        # Change the job_template inventory to match cloud_group
        # Enable host_config_key
        job_template.patch(inventory=cloud_group.inventory, host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # FIXME - should we add a host so the job+callback actually succeed?
        # variables=json.dumps(dict(ansible_ssh_host=ansible_default_ipv4, ansible_connection="local"))

        # Enable update_on_launch
        cloud_group.get_related('inventory_source').patch(update_on_launch=True)

        # Assert that the cloud_group has not updated
        assert cloud_group.get_related('inventory_source').last_updated is None

        # issue callback (expected to return 400)
        args = dict(method="POST",
                    timeout=60,
                    status_code=[httplib.ACCEPTED, httplib.BAD_REQUEST],
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # Assert successful callback
        for result in contacted.values():
            assert 'failed' not in result, "Callback failed\n%s" % result
            assert 'status' in result, "Unexpected callback response"
            assert result['status'] in [httplib.ACCEPTED, httplib.BAD_REQUEST]
            assert not result['changed']

        # NOTE: We don't enforce that a matching system exists in the provided
        # cloud, so it's possible the callback fails to find a matching system.
        # However, it should have initiated an inventory update.
        # assert result['json']['msg'] == 'No matching host could be found!'

        # NOTE: We can't guarruntee that any cloud instances are running, so we
        # don't assert that cloud hosts were imported.
        # assert cloud_group.get_related('hosts').count > 0, "No hosts found " \
        #    "after inventory_update.  An inventory_update was not triggered by " \
        #    "the callback as expected"

        # NOTE: We can't guarruntee that any cloud instances are running.
        # Also, not all cloud inventory scripts create groups when no hosts are
        # found. Therefore, we no longer assert that child groups were created.
        # assert cloud_group.get_related('children').count > 0, "No child groups " \
        #    "found after inventory_update.  An inventory_update was not " \
        #    "triggered by the callback as expected"

        # Assert that the inventory_update is marked as successful
        inv_source_pg = cloud_group.get_related('inventory_source')
        assert inv_source_pg.is_successful, "An inventory_update was launched, but the inventory_source is not successful - %s" % inv_source_pg

        # Assert that an inventory_update completed successfully
        inv_update_pg = inv_source_pg.get_related('last_update')
        assert inv_update_pg.is_successful, "An inventory_update was launched, but did not succeed - %s" % inv_update_pg

    def test_launch_without_inventory_update(self, ansible_runner, job_template, host_config_key, cloud_group, ansible_default_ipv4):
        '''Assert that a callback job against a job_template does not initiate an inventory_update'''

        # Change the job_template inventory to match cloud_group
        # Enable host_config_key
        job_template.patch(inventory=cloud_group.inventory, host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # FIXME - should we add a host so the job+callback actually succeed?
        # variables=json.dumps(dict(ansible_ssh_host=ansible_default_ipv4, ansible_connection="local"))

        # Enable update_on_launch
        cloud_group.get_related('inventory_source').patch(update_on_launch=False)

        # Assert that the cloud_group has not updated
        assert cloud_group.get_related('inventory_source').last_updated is None

        # issue callback (expected to return 400)
        args = dict(method="POST",
                    timeout=60,
                    status_code=[httplib.ACCEPTED, httplib.BAD_REQUEST],
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        contacted = ansible_runner.uri(**args)

        # assert callback response
        for result in contacted.values():
            assert result['status'] in [httplib.ACCEPTED, httplib.BAD_REQUEST]
            assert 'failed' not in result, "Callback failed\n%s" % result
            assert not result['changed']
            # Note, for this test, it is expected that no host will match
            assert result['json']['msg'] == 'No matching host could be found!'

        assert cloud_group.get_related('hosts').count == 0, "Hosts found.  An inventory_update was unexpectedly triggered by the callback"
        assert cloud_group.get_related('children').count == 0, "Children found.  An inventory_update was unexpectedly triggered by the callback"

        # Assert that the cloud_group has not updated
        assert cloud_group.get_related('inventory_source').last_updated is None
