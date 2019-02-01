import functools


from contextlib import contextmanager
import subprocess

from towerkit.utils import random_title
from towerkit import config
import pytest


def format_ev(extra_vars):
    # NOTE: very important that the key=value string use single quotes overall
    # and double quotes for the value, when the value has spaces in it
    return ' '.join(
        '-e {3}{0}={2}{1}{2}{3}'.format(k, v, "'", '"') for k, v in extra_vars.items()
    )


def _run_create_venv_playbook(folder_name=None, limit='tower', packages='python-memcached psutil', use_python=None, docker=False, inv_path=''):
    extra_vars = {
        'venv_folder_name': folder_name,
        'venv_packages': packages,
        'use_become': not docker
    }
    if docker:
        # AWX user not allowed to install software in containers
        extra_vars['ansible_user'] = 0
        extra_vars['venv_base'] = '/venv'
    if use_python is not None:
        extra_vars['remote_python'] = use_python
    cmd = (u"""ansible-playbook -v -i {} -l {} {} playbooks/create_custom_virtualenv.yml"""
           .format(inv_path, limit, format_ev(extra_vars)))
    rc = subprocess.call(cmd, shell=True)
    assert rc == 0, "Received non-zero response code from '{}'".format(cmd)


def _run_teardown_venv_playbook(folder_name=None, limit='tower', use_python=None, docker=False, inv_path=''):
    if not config.prevent_teardown:
        extra_vars = {
            'venv_folder_name': folder_name,
            'use_become': not docker,
            'remove_virtualenv': 'true'
        }
        if docker:
            extra_vars['ansible_user'] = 0
            extra_vars['venv_base'] = '/venv'
        cmd = (u"ansible-playbook -i {} -l {} {} "
               "playbooks/create_custom_virtualenv.yml"
               .format(inv_path, limit, format_ev(extra_vars)))
        rc = subprocess.call(cmd, shell=True)
        assert rc == 0, "Received non-zero response code from '{}'".format(cmd)


@pytest.fixture(scope='class')
def venv_path(is_docker):
    def _venv_path(folder_name='ansible'):
        if is_docker:
            base = '/venv/{}/'
        else:
            base = '/var/lib/awx/venv/{}/'
        return base.format(folder_name)
    return _venv_path


@pytest.fixture(scope='function')
def create_venv(request, venv_path, is_docker):
    inv_path = request.config.getoption('--ansible-inventory')

    @contextmanager
    def _create_venv(folder_name=None, packages='python-memcached psutil', cluster=False, use_python=None):
        if not folder_name:
            folder_name = random_title(non_ascii=False)
        limit = 'instance_group_ordinary_instances' if cluster else 'tower'
        try:
            _run_create_venv_playbook(folder_name, limit, packages, use_python, is_docker, inv_path)
            yield venv_path(folder_name)
        finally:
            # If user is running with teardown prevention on, then leave the
            # virtual environments in-tact.
            _run_teardown_venv_playbook(folder_name, limit, use_python, is_docker, inv_path)
    return _create_venv


@pytest.fixture(scope='class')
def shared_custom_venvs(request, venv_path, is_docker):
    """Create custom venvs to be shared by whole class and tear down after.

       For classes using this fixture, provide a list of dictionaries that
       define the venvs to be created like this:

       Example:

       CUSTOM_VENVS = [
           {
           'name': 'python2_ansible23',
           'packages': 'psutil python-memcached ansible==2.3',
           'python_interpreter': 'python2'
           },
           {
           'name': 'python2_ansibledevel',
           'packages': 'psutil python-memcached git+https://github.com/ansible/ansible.git',
           'python_interpreter': 'python2'
           },
           ]

           @pytest.mark.fixture_args(venvs=CUSTOM_VENVS, cluster=True)
           @pytest.mark.usefixtures(
               'shared_custom_venvs'
           )
           class TestCustomVirtualenvTraditionalCluster(APITest):
               ...
    """
    inv_path = request.config.getoption('--ansible-inventory')
    fixture_args = request.node.get_closest_marker('fixture_args')
    venv_paths = []
    if not fixture_args:
        pytest.fail('''
            Must provide "venvs" to create in fixture_args!
            See doc string of this fixture for more details on usage.
            ''')
    else:
        cluster = fixture_args.kwargs.get('cluster', False)
        limit = 'instance_group_ordinary_instances' if cluster else 'tower'
        if is_docker:
            limit = 'tower'
        if 'venvs' not in fixture_args.kwargs.keys():
            pytest.fail('''
            Must provide "venvs" to create in fixture_args!
            See doc string of this fixture for more details on usage.
            ''')
        else:
            for venv_info in fixture_args.kwargs['venvs']:
                venv_name = venv_info['name']
                packages = venv_info['packages']
                use_python = venv_info['python_interpreter']
                setup_playbook_args = [
                       venv_name,
                       limit,
                       packages,
                       use_python,
                       is_docker,
                       inv_path
                       ]
                teardown_playbook_args = [
                       venv_name,
                       limit,
                       use_python,
                       is_docker,
                       inv_path
                       ]
                teardown_venv = functools.partial(
                    _run_teardown_venv_playbook, *teardown_playbook_args
                    )
                if not config.prevent_teardown:
                    request.addfinalizer(teardown_venv)
                try:
                    _run_create_venv_playbook(*setup_playbook_args)
                    venv_paths.append(venv_path(venv_name))
                except AssertionError as e:
                    pytest.fail(
                        'Failed to create {} with packages {} using python interpreter {}:\n{}'.format(
                            venv_name, packages, use_python, e
                            )
                        )
        return venv_paths
