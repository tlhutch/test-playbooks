from contextlib import contextmanager
import subprocess

from towerkit.utils import random_title
import pytest


@pytest.fixture(scope='function')
def venv_path():
    def _venv_path(folder_name='ansible'):
        return '/var/lib/awx/venv/{}/'.format(folder_name)
    return _venv_path


@pytest.fixture(scope='function')
def create_venv(venv_path, hosts_in_group, hostvars_for_host):
    @contextmanager
    def _create_venv(folder_name=None, packages='python-memcached psutil', cluster=False):
        if not folder_name:
            folder_name = random_title(non_ascii=False)
        if cluster:
            hosts = hosts_in_group('instance_group_ordinary_instances')
            host_username_mapping = {host: hostvars_for_host(host).get('ansible_user') for host in hosts}
        else:
            hosts = hosts_in_group('tower')
            host_username_mapping = {hosts[0]: hostvars_for_host(hosts[0]).get('ansible_user')}
        try:
            for host in hosts:
                cmd = (u"""ansible-playbook -u {} -i {}, -e venv_folder_name={} -e "venv_packages='{}'" playbooks/create_custom_virtualenv.yml"""
                       .format(host_username_mapping[host], host, folder_name, packages))
                rc = subprocess.call(cmd, shell=True)
                assert rc == 0, "Received non-zero response code from '{}'".format(cmd)
            yield venv_path(folder_name)
        finally:
            for host in hosts:
                cmd = (u"ansible-playbook -u {} -i {}, -e venv_folder_name={} -e remove_virtualenv=true "
                       "playbooks/create_custom_virtualenv.yml"
                       .format(host_username_mapping[host], host, folder_name))
                rc = subprocess.call(cmd, shell=True)
                assert rc == 0, "Received non-zero response code from '{}'".format(cmd)
    return _create_venv
