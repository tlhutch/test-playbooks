import socket
import requests
import os
import pytest

from towerkit import config
import towerkit.exceptions as exc

from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestJobTemplateProvisionCallback(Base_Api_Test):

    @pytest.fixture
    def remote_hosts(self):
        hosts = ['gateway'] # Docker dev env remote
        hosts.append(socket.gethostbyname(socket.gethostname())) # Network Interface
        hosts.append(requests.get('https://api.ipify.org').text) # External IP
        return hosts

    @pytest.fixture
    def host_config_key(self):
        return 'foobar123'

    def get_job_id_from_location_header(self, resp):
        return os.path.basename(os.path.normpath(resp.headers['Location']))

    @pytest.fixture
    def job_template_with_host_config_key(self, factories, remote_hosts, host_config_key):
        jt = factories.v2_job_template(host_config_key=host_config_key)
        map(lambda h: factories.v2_host(inventory=jt.ds.inventory,
                                        name=h,
                                        variables=dict(ansible_host=h, ansible_connection='local')), remote_hosts)
        return jt

    def test_provision_callback_success(self, job_template_with_host_config_key, host_config_key, remote_hosts):
        jt = job_template_with_host_config_key
        res = requests.post("{}{}".format(config.base_url, jt.related.callback),
                            data={'host_config_key': host_config_key})
        assert res.status_code == 201, \
                "Launching Job Template via provision callback failed. Remote host list {}".format(remote_hosts)

    def test_provision_callback_user_relaunch_forbidden(self, v2, factories, job_template_with_host_config_key, host_config_key, remote_hosts):
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
            with pytest.raises(exc.Forbidden) as e:
                job1.relaunch()

        assert 'Job was launched with prompts provided by another user.' == e.value.message['detail']
