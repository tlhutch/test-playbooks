from urlparse import urlparse
import httplib
import socket
import json
import requests
import os

from towerkit.config import config
from towerkit import utils, exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateCallbacks(Base_Api_Test):
    @pytest.fixture
    def remote_hosts(self):
        hosts = ['gateway'] # Docker dev env remote
        hosts.append(socket.gethostbyname(socket.gethostname())) # Network Interface
        hosts.append(requests.get('https://api.ipify.org').text) # External IP
        return hosts

    def get_job_id_from_location_header(self, resp):
        return os.path.basename(os.path.normpath(resp.headers['Location']))

    @pytest.fixture
    def job_template_with_host_config_key(self, factories, remote_hosts, host_config_key):
        limits = ','.join(remote_hosts)
        jt = factories.v2_job_template(host_config_key=host_config_key, limits=limits)
        map(lambda h: factories.v2_host(inventory=jt.ds.inventory,
                                        name=h,
                                        variables=dict(ansible_host=h, ansible_connection='local')), remote_hosts)
        return jt

    def test_assignment_of_host_config_key(self, job_template, host_config_key):
        """Confirm that when a job template's host config key is set, it is exposed through JT and callback endpoint"""
        job_template.host_config_key = host_config_key
        assert job_template.host_config_key == host_config_key

        callback = job_template.get_related('callback')
        assert callback.host_config_key == host_config_key

    def test_matching_hosts_empty_in_nonmember_query(self, factories, host_config_key):
        """Assert a GET on the callback resource returns an empty list of matching hosts when made by a nonmember"""
        host = factories.host(variables=json.dumps(dict(ansible_host='169.254.1.0')))
        job_template = factories.job_template(inventory=host.ds.inventory)

        job_template.host_config_key = host_config_key
        callback = job_template.get_related('callback')
        assert len(callback.matching_hosts) == 0

    @pytest.fixture(scope='class')
    def callback_host(self, ansible_module_cls, is_docker):
        base_url = urlparse(config.base_url)
        port = '' if base_url.port is None else ':{0.port}'.format(base_url)
        scheme = 'http' if base_url.scheme is None else base_url.scheme
        host = 'localhost' if is_docker else base_url.hostname
        return '{0}://{1}{2}'.format(scheme, host, port)

    @pytest.mark.skip_openshift
    def test_matching_hosts_contains_member_in_member_query(self, ansible_runner, host_config_key, job_template,
                                                            host_with_default_ipv4_in_variables, callback_host):
        """Assert a GET on the callback resource returns a list containing a matching host if made by that host"""
        job_template.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="GET",
                                       status_code=httplib.OK,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       user=config.credentials.users.admin.username,
                                       password=config.credentials.users.admin.password,
                                       force_basic_auth=True,
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.OK
        assert not result['changed']
        assert not result.get('failed')

        matching_hosts = contacted.values()[0]['json']['matching_hosts']
        assert len(matching_hosts) == 1
        # account for dev container
        desired_hostname = 'local' if 'localhost' in callback_host else host_with_default_ipv4_in_variables.name
        assert matching_hosts[0] == desired_hostname

    @pytest.mark.skip_openshift
    def test_provision_failure_with_empty_inventory(self, ansible_runner, factories, host_config_key, callback_host):
        """Verify launch failure when called on a job template with an empty inventory"""
        job_template = factories.job_template()
        job_template.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.BAD_REQUEST
        assert result.get('failed', True)
        assert result['json']['msg'] == 'No matching host could be found!'

    @pytest.mark.github('https://github.com/ansible/tower/issues/958')
    def test_provision_failure_with_null_inventory(self, host_config_key, job_template):
        """Verify launch failure when called on a job template has no associated inventory"""
        job_template.host_config_key = host_config_key
        with pytest.raises(exc.BadRequest) as e:
            job_template.inventory = None
        assert 'Cannot enable provisioning callback without an inventory set.' in str(e)

    @pytest.fixture(scope="function")
    def hosts_with_actual_ipv4_for_name_and_random_ssh_host(self, request, factories, group, callback_host):
        """Create an inventory host matching the public ipv4 address of the system running pytest."""
        if 'localhost' in callback_host:  # account for dev container
            local_ipv4_addresses = ['127.0.0.1', 'localhost']
        else:
            local_ipv4_addresses = socket.gethostbyname_ex(socket.gethostname())[2]

        hosts = []
        for ipv4_addr in local_ipv4_addresses:
            host = factories.host(name=ipv4_addr, inventory=group.ds.inventory,
                                  variables=json.dumps(dict(ansible_host=utils.random_ipv4(),
                                                            ansible_connection="local")))
            group.add_host(host)
            hosts.append(host)

        return hosts

    @pytest.mark.skip_openshift
    def test_provision_failure_with_non_matching_ssh_host(self, ansible_runner, factories, host_config_key,
                                                          hosts_with_actual_ipv4_for_name_and_random_ssh_host,
                                                          callback_host):
        """Verify launch failure when a matching host.name is found, but ansible_host is different."""
        inventory = hosts_with_actual_ipv4_for_name_and_random_ssh_host[0].ds.inventory
        job_template = factories.job_template(inventory=inventory)
        job_template.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert 'status' in result
        assert result['status'] == httplib.BAD_REQUEST
        assert result.get('failed', True)
        assert result['json']['msg'] == 'No matching host could be found!'

    @pytest.mark.skip_openshift
    def test_provision_failure_with_multiple_host_matches(self, ansible_runner, factories, ansible_default_ipv4,
                                                          host_config_key, callback_host):
        """Verify launch failure when launching a job_template where multiple hosts match"""
        inventory = factories.inventory()

        # account for dev container
        ansible_host = '127.0.0.1' if 'localhost' in callback_host else ansible_default_ipv4
        for name in ('matching_host', 'another_matching_host'):
            factories.host(name=name, inventory=inventory,
                           variables=json.dumps(dict(ansible_host=ansible_host,
                                                     ansible_connection="local")))

        job_template = factories.job_template(inventory=inventory)
        job_template.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.BAD_REQUEST
        assert result.get('failed', True)
        assert result['json']['msg'] == 'Multiple hosts matched the request!'

    @pytest.mark.skip_openshift
    def test_provision_failure_with_incorrect_hostkey(self, ansible_runner, job_template,
                                                      host_with_default_ipv4_in_variables, host_config_key,
                                                      callback_host):
        """Verify launch failure when providing incorrect host_config_key"""
        job_template.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json',
                                       body=dict(host_config_key='BOGUS'),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.FORBIDDEN
        assert result.get('failed', True)
        assert result['json']['detail'] == 'You do not have permission to perform this action.'

    @pytest.mark.skip_openshift
    def test_provision_failure_without_credential(self, ansible_runner, job_template_no_credential,
                                                  host_with_default_ipv4_in_variables, host_config_key, callback_host):
        """Verify launch failure when launching a job_template with no credentials"""
        job_template_no_credential.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template_no_credential),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.BAD_REQUEST
        assert result.get('failed', True)
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    @pytest.mark.skip_openshift
    def test_provision_failure_with_ask_credential(self, ansible_runner, job_template_ask,
                                                   host_with_default_ipv4_in_variables, host_config_key, callback_host):
        """Verify launch failure when launching a job_template with ASK credentials"""
        job_template_ask.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template_ask),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.BAD_REQUEST
        assert result.get('failed', True)
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    @pytest.mark.skip_openshift
    def test_provision_failure_with_unprovided_survey_variables_needed_to_start(self, ansible_runner,
                                                                                job_template_variables_needed_to_start,
                                                                                host_with_default_ipv4_in_variables,
                                                                                host_config_key, callback_host):
        """Verify launch failure when launching a job_template that has required survey variables."""
        job_template_variables_needed_to_start.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host,
                                                                            job_template_variables_needed_to_start),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.BAD_REQUEST
        assert result.get('failed', True)
        assert result['json']['msg'] == 'Cannot start automatically, user input required!'

    @pytest.mark.skip_openshift
    def test_provision_with_provided_variables_needed_to_start(self, ansible_runner,
                                                               job_template_variables_needed_to_start,
                                                               host_with_default_ipv4_in_variables, host_config_key,
                                                               callback_host):
        """Verify launch success when launching a job_template while providing required survey variables."""
        job_template_variables_needed_to_start.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host,
                                                                            job_template_variables_needed_to_start),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key,
                                                 extra_vars=dict(likes_chicken='yes',
                                                                 favorite_color='red')),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.CREATED
        assert not result['changed']
        assert not result.get('failed')

        job_id = result['location'].split('jobs/')[1].split('/')[0]
        job = job_template_variables_needed_to_start.related.jobs.get(id=job_id).results.pop().wait_until_completed()
        assert job.launch_type == "callback"
        assert job.is_successful

    @pytest.mark.skip_openshift
    def test_provision_job_template_with_limit(self, api_jobs_url, ansible_runner, job_template_with_random_limit,
                                               host_with_default_ipv4_in_variables, host_config_key, callback_host):
        """Assert that launching a callback job against a job_template with an
        existing 'limit' parameter successfully launches and that it is launched
        with a value for "limit" that matches our test host.
        """
        job_template_with_random_limit.host_config_key = host_config_key

        contacted = ansible_runner.uri(method="POST",
                                       timeout=60,
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host,
                                                                            job_template_with_random_limit),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.CREATED
        assert not result['changed']
        assert not result.get('failed')

        job_id = result['location'].split('jobs/')[1].split('/')[0]
        job = job_template_with_random_limit.related.jobs.get(id=job_id).results.pop().wait_until_completed()
        assert job.launch_type == "callback"
        assert job.is_successful

        # account for dev container
        desired_hostname = 'local' if 'localhost' in callback_host else host_with_default_ipv4_in_variables.name
        assert job.limit == desired_hostname

    @pytest.mark.skip_openshift
    @pytest.mark.parametrize(
        'ask_on_launch,provided_extra_vars,expected_extra_vars',
        [[False, {}, {}],
         [False, dict(dont_filter_me=True, ansible_filter_me=1234), {}],
         [True, dict(dont_filter_me=True, ansible_filter_me=1234), dict(dont_filter_me=True)],
         [False, "{\"dont_filter_me\": true, \"ansible_filter_me\": 1234}", {}],
         [True, "{\"dont_filter_me\": true, \"ansible_filter_me\": 1234}", dict(dont_filter_me=True)],
         [False, '---\ndont_filter_me: true\nansible_filter_me: 1234', {}],
         [True, '---\ndont_filter_me: true\nansible_filter_me: 1234', dict(dont_filter_me=True)]]
    )
    def test_provision_with_provided_extra_vars(self, ansible_runner, job_template, host_with_default_ipv4_in_variables,
                                                host_config_key, ask_on_launch, provided_extra_vars,
                                                expected_extra_vars, callback_host):
        """Confirms that provided extra_vars in callback request are properly accepted and filtered/ignored"""
        job_template.host_config_key = host_config_key
        job_template.ask_variables_on_launch = ask_on_launch

        contacted = ansible_runner.uri(method="POST", timeout=90, status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json', validate_certs=False,
                                       body=dict(host_config_key=host_config_key, extra_vars=provided_extra_vars))

        result = contacted.values().pop()
        assert result['status'] == httplib.CREATED
        assert not result['changed']
        assert not result.get('failed')

        job_id = result['location'].split('jobs/')[1].split('/')[0]
        job = job_template.related.jobs.get(id=job_id).results.pop().wait_until_completed()
        assert job.launch_type == "callback"
        assert job.is_successful

        host_summaries = job.related.job_host_summaries.get()
        assert host_summaries.count == 1

        # account for dev container
        desired_id = host_with_default_ipv4_in_variables.id
        if 'localhost' in callback_host:
            inventory = host_with_default_ipv4_in_variables.ds.inventory
            desired_id = inventory.related.hosts.get(name='local').results.pop().id
        assert host_summaries.results[0].host == desired_id
        assert json.loads(job.extra_vars) == expected_extra_vars

    @pytest.mark.skip_openshift
    def test_provision_without_required_extra_vars(self, ansible_runner, job_template,
                                                   host_with_default_ipv4_in_variables,
                                                   host_config_key, callback_host):
        """Confirms that launch attempts for `ask_variables_on_launch` jobs fail without extra_vars"""
        job_template.host_config_key = host_config_key
        job_template.ask_variables_on_launch = True

        contacted = ansible_runner.uri(method="POST", timeout=90, status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json', validate_certs=False,
                                       body=dict(host_config_key=host_config_key))

        callback_result = contacted.values().pop()
        assert callback_result['status'] == httplib.BAD_REQUEST
        assert callback_result.get('failed', True)
        assert callback_result['json']['msg'] == 'Cannot start automatically, user input required!'

    @pytest.mark.skip_openshift
    def test_provision_failure_with_currently_running_and_simultaneous_disallowed(
            self, api_jobs_url, ansible_runner, job_template,
            host_with_default_ipv4_in_variables, host_config_key,
            callback_host
        ):
        """Verify that issuing a callback, while a callback job from the same host is already running, fails."""
        job_template.patch(host_config_key=host_config_key,
                           playbook='sleep.yml',
                           extra_vars='{"sleep_interval": 10}')

        for attempt in range(3):
            contacted = ansible_runner.uri(method="POST",
                                           timeout=60,
                                           status_code=httplib.CREATED,
                                           url='{0}{1.related.callback}'.format(callback_host, job_template),
                                           body_format='json',
                                           body=dict(host_config_key=host_config_key),
                                           validate_certs=False)

            result = contacted.values().pop()
            if attempt == 0:
                assert result['status'] == httplib.CREATED
                assert not result['changed']
                assert not result.get('failed')
                job_id = result['location'].split('jobs/')[1].split('/')[0]
            else:
                assert result['status'] == httplib.BAD_REQUEST
                assert result.get('failed', True)

        job = job_template.related.jobs.get(id=job_id).results.pop().wait_until_completed()
        assert job.launch_type == "callback"
        assert job.is_successful

        host_summaries = job.get_related('job_host_summaries')
        assert host_summaries.count == 1

        # account for dev container
        desired_id = host_with_default_ipv4_in_variables.id
        if 'localhost' in callback_host:
            inventory = host_with_default_ipv4_in_variables.ds.inventory
            desired_id = inventory.related.hosts.get(name='local').results.pop().id
        assert host_summaries.results[0].host == desired_id

    @pytest.mark.skip_openshift
    def test_synced_host_provision_with_inventory_update_on_launch(self, ansible_runner, factories, host_config_key,
                                                                    ansible_default_ipv4, callback_host):
        """Confirms that when a provisioning host is loaded from an update_on_launch-generated inventory sync
        the job runs successfully against that host.
        """
        ansible_host = '127.0.0.1' if 'localhost' in callback_host else ansible_default_ipv4
        script = '\n'.join([
            u'#!/usr/bin/env python',
            u'# -*- coding: utf-8 -*-',
            u'import json',
            u'inventory = dict()',
            u'inventory["some_group"] = dict()',
            u'inventory["some_group"]["hosts"] = ["{}"]',
            u'inventory["some_group"]["vars"] = dict(ansible_connection="local")',
            u'print json.dumps(inventory)'
        ]).format(ansible_host)

        inv_script = factories.v2_inventory_script(script=script)
        custom_source = factories.v2_inventory_source(inventory_script=inv_script)
        custom_source.update_on_launch = True

        job_template = factories.v2_job_template(inventory=custom_source.ds.inventory)
        job_template.host_config_key = host_config_key

        assert custom_source.last_updated is None

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert not result.get('failed')
        assert result['status'] == httplib.CREATED
        assert not result['changed']
        job_id = result['location'].split('jobs/')[1].split('/')[0]
        job = job_template.related.jobs.get(id=job_id).results.pop().wait_until_completed()
        assert job.is_successful

        assert custom_source.get().is_successful
        assert custom_source.related.last_update.get().is_successful

        host_summaries = job.related.job_host_summaries.get().results
        assert len(host_summaries) == 1
        assert host_summaries[0].related.host.get().name == ansible_host

    @pytest.mark.skip_openshift
    def test_member_host_provision_with_inventory_update_on_launch(self, ansible_runner, factories, host_config_key,
                                                                    ansible_default_ipv4, callback_host):
        """Confirms that when a provisioning host is already in an inventory an update_on_launch inventory sync
        still runs and the job runs successfully against that host.
        """
        script = '\n'.join([
            u'#!/usr/bin/env python',
            u'# -*- coding: utf-8 -*-',
            u'import json',
            u'inventory = dict()',
            u'inventory["some_group"] = dict()',
            u'inventory["some_group"]["hosts"] = ["169.254.1.0"]',
            u'print json.dumps(inventory)'
        ])

        inv_script = factories.v2_inventory_script(script=script)
        custom_source = factories.v2_inventory_source(inventory_script=inv_script)
        custom_source.update_on_launch = True

        ansible_host = '127.0.0.1' if 'localhost' in callback_host else ansible_default_ipv4
        factories.v2_host(name=ansible_host, inventory=custom_source.ds.inventory,
                          variables=dict(ansible_host=ansible_host, ansible_connection='local'))

        job_template = factories.v2_job_template(inventory=custom_source.ds.inventory)
        job_template.host_config_key = host_config_key

        assert custom_source.last_updated is None

        contacted = ansible_runner.uri(method="POST",
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert not result.get('failed')
        assert result['status'] == httplib.CREATED
        assert not result['changed']
        job_id = result['location'].split('jobs/')[1].split('/')[0]
        job = job_template.related.jobs.get(id=job_id).results.pop().wait_until_completed()
        assert job.is_successful

        assert custom_source.get().is_successful
        assert custom_source.related.last_update.get().is_successful

        host_summaries = job.related.job_host_summaries.get().results
        assert len(host_summaries) == 1
        assert host_summaries[0].related.host.get().name == ansible_host

    @pytest.mark.skip_openshift
    def test_provision_without_inventory_update_on_launch(self, ansible_runner, factories, host_config_key,
                                                          custom_group, ansible_default_ipv4, callback_host):
        """Assert that a callback job against a job_template does not initiate an inventory_update"""
        inventory = custom_group.ds.inventory
        ansible_host = '127.0.0.1' if 'localhost' in callback_host else ansible_default_ipv4
        factories.host(name='callback_host', inventory=inventory,
                       variables=json.dumps(dict(ansible_host=ansible_host,
                                                 ansible_connection="local")))

        job_template = factories.job_template(inventory=inventory)
        job_template.host_config_key = host_config_key

        custom_group.related.inventory_source.patch(update_on_launch=False)

        assert custom_group.get_related('inventory_source').last_updated is None

        contacted = ansible_runner.uri(method="POST",
                                       timeout=60,
                                       status_code=httplib.CREATED,
                                       url='{0}{1.related.callback}'.format(callback_host, job_template),
                                       body_format='json',
                                       body=dict(host_config_key=host_config_key),
                                       validate_certs=False)

        result = contacted.values().pop()
        assert result['status'] == httplib.CREATED
        assert not result.get('failed')
        assert not result['changed']
        job_id = result['location'].split('jobs/')[1].split('/')[0]
        job_template.related.jobs.get(id=job_id).results.pop().wait_until_completed()

        assert custom_group.get_related('hosts').count == 0
        assert custom_group.get_related('children').count == 0
        assert custom_group.get_related('inventory_source').last_updated is None

    def test_provision_callback_user_relaunch_forbidden(self, v2, factories, job_template_with_host_config_key, host_config_key, remote_hosts):
        """
        Provision callback launched job implicitly uses the limit field. This
        falls in the class of a "parameter" used to launch the job. Job's launched
        with a parameter are not re-launchable by other users because of sensitive
        data considerations. BUT, relaunching a provision callback job is an exception
        because Tower can fully know that relaunch contains no sensitive data. Thus,
        we allow relaunch in the case described.
        """
        jt = job_template_with_host_config_key
        res = requests.post("{}{}".format(config.base_url, jt.related.callback),
                            data={'host_config_key': host_config_key})
        assert res.status_code == 201, \
                "Launching Job Template via provision callback failed. Remote host list {}".format(remote_hosts)

        job_id = self.get_job_id_from_location_header(res)
        job1 = v2.jobs.get(id=job_id).results[0]

        user = factories.v2_user()
        jt.ds.inventory.ds.organization.set_object_roles(user, 'member')
        map(lambda resource: jt.ds[resource].set_object_roles(user, 'use'), ['credential', 'project', 'inventory'])
        jt.set_object_roles(user, 'execute')

        with self.current_user(user):
            job1.relaunch()
