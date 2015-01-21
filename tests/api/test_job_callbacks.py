import re
import pytest
import httplib
import json
import common.utils
import common.exceptions
from tests.api import Base_Api_Test


@pytest.fixture(scope="function")
def host_ipv4_again(request, authtoken, api_hosts_pg, host_ipv4):
    '''Create a another host object matching host_ipv4'''
    payload = host_ipv4.json
    payload.update(name="host_ipv4_again - %s" % common.utils.random_ascii(),)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group(s)
    for group in host_ipv4.get_related('groups').results:
        with pytest.raises(common.exceptions.NoContent_Exception):
            obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.fixture(scope="function")
def host_public_ipv4_alias(request, authtoken, api_hosts_pg, group, my_public_ipv4):
    '''Create an inventory host matching the public ipv4 address of the system running pytest, but use a random ipv4 address'''
    payload = dict(name=my_public_ipv4,
                   description="test host %s" % common.utils.random_unicode(),
                   variables=json.dumps(dict(ansible_ssh_host=common.utils.random_ipv4(), ansible_connection="local")),
                   inventory=group.inventory,)
    obj = api_hosts_pg.post(payload)
    request.addfinalizer(obj.delete)
    # Add to group
    with pytest.raises(common.exceptions.NoContent_Exception):
        obj.get_related('groups').post(dict(id=group.id))
    return obj


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_Callback(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'backup_license', 'install_license_1000')

    def test_get(self, job_template, host_config_key, host_public_ipv4, host_ipv4):
        '''Assert a GET on the /callback resource returns a list of matching hosts'''
        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # Assert the GET response includes the proper host_config_key
        callback_pg = job_template.get_related('callback')
        assert callback_pg.host_config_key == host_config_key

        # Assert the GET response includes expected inventory counts
        all_inventory_hosts = host_public_ipv4.get_related('inventory').get_related('hosts')
        assert all_inventory_hosts.count == 2, "Unexpected number of inventory_hosts (%s != 2)" % all_inventory_hosts.count
        assert len(callback_pg.matching_hosts) == 1, "Unexpected number of matching_hosts (%s != 1)" % len(callback_pg.matching_hosts)

        # Assert the GET response includes expected values in matching_hosts
        assert host_public_ipv4.name in callback_pg.matching_hosts
        assert host_ipv4.name not in callback_pg.matching_hosts

    def test_launch_with_no_hosts(self, ansible_runner, job_template, host_config_key, ansible_default_ipv4):
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
        result = ansible_runner.uri(**args)

        # verify callback response
        assert result['status'] == httplib.BAD_REQUEST, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.BAD_REQUEST, result)
        assert result['failed']
        assert result['json']['msg'] == 'No matching host could be found!'

    def test_launch_with_no_matching_hosts(self, ansible_runner, job_template, host_config_key, ansible_default_ipv4, host_public_ipv4_alias):
        '''Verify launch failure when a matching host.name is found, but ansible_ssh_host is different.'''
        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert 'status' in result, "Unxpected response: %s" % result
        assert result['status'] == httplib.BAD_REQUEST, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.BAD_REQUEST, result)
        assert result['failed']
        assert result['json']['msg'] == 'No matching host could be found!'

    def test_launch_multiple_host_matches(self, ansible_runner, job_template, host_ipv4, host_ipv4_again, host_config_key, ansible_default_ipv4):
        '''Verify launch failure when launching a job_template where multiple hosts match '''

        # enable callback
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        args = dict(method="POST",
                    status_code=httplib.ACCEPTED,
                    url="http://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback']),
                    body="host_config_key=%s" % host_config_key,)
        args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
        result = ansible_runner.uri(**args)

        assert result['status'] == httplib.BAD_REQUEST
        assert 'failed' in result and result['failed']
        assert result['json']['msg'] == 'Multiple hosts matched the request!'

    def test_launch_with_incorrect_hostkey(self, ansible_runner, job_template, host_ipv4, host_config_key, ansible_default_ipv4):
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
        result = ansible_runner.uri(**args)

        # verify callback response
        assert result['status'] == httplib.FORBIDDEN, "Unexpected response code (%s!=%s)\n%s" % (result['status'], httplib.FORBIDDEN, result)
        assert result['failed']
        assert result['json']['detail'] == 'You do not have permission to perform this action.'

    def test_launch_without_credential(self, ansible_runner, job_template_no_credential, host_ipv4, host_config_key, ansible_default_ipv4):
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
        result = ansible_runner.uri(**args)

        # verify callback response
        assert result['status'] == httplib.BAD_REQUEST
        assert result['failed']
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_with_ask_credential(self, ansible_runner, job_template_ask, host_ipv4, host_config_key, ansible_default_ipv4):
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
        result = ansible_runner.uri(**args)

        # verify callback response
        assert result['status'] == httplib.BAD_REQUEST
        assert result['failed']
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_with_variables_needed_to_start(self, ansible_runner, job_template_variables_needed_to_start, host_ipv4, host_config_key, ansible_default_ipv4):
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
        result = ansible_runner.uri(**args)

        # verify callback response
        assert result['status'] == httplib.BAD_REQUEST
        assert result['failed']
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    def test_launch_with_limit(self, api_jobs_url, ansible_runner, job_template_with_limit, host_ipv4, host_config_key, ansible_default_ipv4):
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
        result = ansible_runner.uri(**args)

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
        error_strings = ["ERROR: Specified --limit does not match any hosts",
                         "ERROR: provided hosts list is empty"]
        assert any([True for errstr in error_strings if errstr in job_pg.result_stdout]), \
            "Unable to find expected error (%s) in job_pg.result_stdout (%s)" % \
            (error_strings, job_pg.result_stdout)

    def test_launch(self, ansible_runner, job_template, host_ipv4, host_config_key, ansible_default_ipv4):
        '''Assert that launching a callback job against a job_template successfully launches, and the job successfully runs on a single host..'''

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
        result = ansible_runner.uri(**args)

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
        host_summaries_pg = job_pg.get_related('job_host_summaries')
        assert host_summaries_pg.count == 1

        # Assert the affected host matches expected
        assert host_summaries_pg.results[0].host == host_ipv4.id

    def test_launch_multiple(self, api_jobs_url, ansible_runner, job_template, host_ipv4, host_config_key, ansible_default_ipv4):
        '''
        Verify that issuing a callback, while a callback job from the same host
        is already running, fails.
        '''

        # enable host_config_key
        job_template.patch(host_config_key=host_config_key)
        assert job_template.host_config_key == host_config_key

        # issue multiple callbacks, only the first should succeed
        for attempt in range(3):
            callback_url = "https://%s/%s" % (ansible_default_ipv4, job_template.json['related']['callback'])
            args = dict(method="POST",
                        timeout=60,
                        status_code=httplib.ACCEPTED,
                        url=callback_url,
                        body="host_config_key=%s" % host_config_key,)
            args["HEADER_Content-Type"] = "application/x-www-form-urlencoded"
            result = ansible_runner.uri(**args)
            print json.dumps(result)

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
        assert host_summaries_pg.results[0].host == host_ipv4.id

    def test_launch_with_inventory_update(self, api_jobs_url, ansible_runner, job_template, host_config_key, cloud_group, ansible_default_ipv4, tower_version_cmp):
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
        result = ansible_runner.uri(**args)
        print json.dumps(result)

        # Assert successful callback
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
        result = ansible_runner.uri(**args)
        print result

        assert result['status'] in [httplib.ACCEPTED, httplib.BAD_REQUEST]
        assert 'failed' not in result, "Callback failed\n%s" % result
        assert not result['changed']
        # Note, for this test, it is expected that no host will match
        assert result['json']['msg'] == 'No matching host could be found!'

        assert cloud_group.get_related('hosts').count == 0, "Hosts found.  An inventory_update was unexpectedly triggered by the callback"
        assert cloud_group.get_related('children').count == 0, "Children found.  An inventory_update was unexpectedly triggered by the callback"

        # Assert that the cloud_group has not updated
        assert cloud_group.get_related('inventory_source').last_updated is None
