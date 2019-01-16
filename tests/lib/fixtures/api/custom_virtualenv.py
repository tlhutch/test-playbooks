from contextlib import contextmanager
import subprocess

from towerkit.utils import random_title
import pytest


@pytest.fixture(scope='function')
def venv_path(is_docker):
    def _venv_path(folder_name='ansible'):
        if is_docker:
            base = '/venv/{}/'
        else:
            base = '/var/lib/awx/venv/{}/'
        return base.format(folder_name)
    return _venv_path


def format_ev(extra_vars):
    # NOTE: very important that the key=value string use single quotes overall
    # and double quotes for the value, when the value has spaces in it
    return ' '.join(
        '-e {3}{0}={2}{1}{2}{3}'.format(k, v, "'", '"') for k, v in extra_vars.items()
    )


@pytest.fixture(scope='function')
def create_venv(request, venv_path, is_docker):
    inv_path = request.config.getoption('--ansible-inventory')

    @contextmanager
    def _create_venv(folder_name=None, packages='python-memcached psutil', cluster=False):
        if not folder_name:
            folder_name = random_title(non_ascii=False)
        if cluster:
            limit = 'instance_group_ordinary_instances'
        else:
            limit = 'tower'
        try:
            extra_vars = {
                'venv_folder_name': folder_name,
                'venv_packages': packages,
                'use_become': not is_docker
            }
            if is_docker:
                # AWX user not allowed to install software in containers
                extra_vars['ansible_user'] = 0
                extra_vars['venv_base'] = '/venv'
            cmd = (u"""ansible-playbook -i {} -l {} {} playbooks/create_custom_virtualenv.yml"""
                   .format(inv_path, limit, format_ev(extra_vars)))
            print('first cmd')
            print(cmd)
            rc = subprocess.call(cmd, shell=True)
            assert rc == 0, "Received non-zero response code from '{}'".format(cmd)
            yield venv_path(folder_name)
        finally:
            extra_vars = {
                'venv_folder_name': folder_name,
                'use_become': not is_docker,
                'remove_virtualenv': 'true'
            }
            if is_docker:
                extra_vars['ansible_user'] = 0
                extra_vars['venv_base'] = '/venv'
            cmd = (u"ansible-playbook -i {} -l {} {} "
                   "playbooks/create_custom_virtualenv.yml"
                   .format(inv_path, limit, format_ev(extra_vars)))
            rc = subprocess.call(cmd, shell=True)
            assert rc == 0, "Received non-zero response code from '{}'".format(cmd)
    return _create_venv
