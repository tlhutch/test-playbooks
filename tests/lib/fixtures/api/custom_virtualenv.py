import functools
import tempfile


from contextlib import contextmanager
import subprocess

from awxkit.utils import random_title
from awxkit import config
import pytest


def format_ev(extra_vars):
    # NOTE: very important that the key=value string use single quotes overall
    # and double quotes for the value, when the value has spaces in it
    return ' '.join(
        '-e {3}{0}={2}{1}{2}{3}'.format(k, v, "'", '"') for k, v in extra_vars.items()
    )


def _call_command(cmd):
    """Call the command ``cmd`` and raise an AssertionError if its return code
    isn't 0.
    """
    with tempfile.TemporaryFile('w+') as stdout, tempfile.TemporaryFile('w+') as stderr:
        rc = subprocess.call(cmd, stdout=stdout, stderr=stderr, shell=True)

        if rc != 0:
            message = [f'Received non-zero response code from "{cmd}"']

            stdout.seek(0)
            output = stdout.read()
            if output:
                message.append(f'stdout:\n\n{output}')
            else:
                message.append(f'stdout: <empty>')

            stderr.seek(0)
            error = stderr.read()
            if error:
                message.append(f'stderr:\n\n{error}')
            else:
                message.append(f'stderr: <empty>')

            raise AssertionError('\n\n'.join(message))


def _run_create_venv_playbook(folder_name=None, limit='tower', packages='psutil', use_python=None, docker=False, inv_path='', custom_venv_base=None):
    extra_vars = {
        'venv_folder_name': folder_name,
        'venv_packages': packages,
        'use_become': not docker
    }
    if docker:
        # AWX user not allowed to install software in containers
        extra_vars['ansible_user'] = 0
        extra_vars['venv_base'] = '/venv'
    if custom_venv_base:
        extra_vars['venv_base'] = custom_venv_base
    if use_python is not None:
        extra_vars['remote_python'] = use_python
        if use_python == 'python3' and not docker:
            extra_vars['remote_python'] = 'python36'
    cmd = ("""ansible-playbook -vv -i {} -l {} {} playbooks/create_custom_virtualenv.yml"""
           .format(inv_path, limit, format_ev(extra_vars)))
    _call_command(cmd)


def _run_teardown_venv_playbook(folder_name=None, limit='tower', use_python=None, docker=False, inv_path='', custom_venv_base=None):
    if not config.prevent_teardown:
        extra_vars = {
            'venv_folder_name': folder_name,
            'use_become': not docker,
            'remove_virtualenv': 'true'
        }
        if docker:
            extra_vars['ansible_user'] = 0
            extra_vars['venv_base'] = '/venv'

        if use_python == 'python3' and not docker:
            extra_vars['remote_python'] = 'python36'

        if custom_venv_base:
            extra_vars['venv_base'] = custom_venv_base

        cmd = ("ansible-playbook -i {} -l {} {} "
               "playbooks/create_custom_virtualenv.yml"
               .format(inv_path, limit, format_ev(extra_vars)))
        _call_command(cmd)


@pytest.fixture(scope='class')
def venv_path(is_dev_container):
    def _venv_path(folder_name='ansible', custom_venv_base=None):
        if custom_venv_base:
            return f'{custom_venv_base}/{folder_name}/'
        if is_dev_container:
            base = '/venv/{}/'
        else:
            base = '/var/lib/awx/venv/{}/'
        return base.format(folder_name)
    return _venv_path


@pytest.fixture(scope='function')
def create_venv(request, venv_path, is_docker):
    inv_path = request.config.getoption('--ansible-inventory')

    @contextmanager
    def _create_venv(folder_name=None, packages='psutil', cluster=False, use_python=None, custom_venv_base=None):
        if not folder_name:
            folder_name = random_title(non_ascii=False)
        limit = 'instance_group_ordinary_instances' if cluster else 'tower'
        try:
            _run_create_venv_playbook(folder_name, limit, packages, use_python, is_docker, inv_path, custom_venv_base)
            yield venv_path(folder_name, custom_venv_base)
        finally:
            # If user is running with teardown prevention on, then leave the
            # virtual environments in-tact.
            _run_teardown_venv_playbook(folder_name, limit, use_python, is_docker, inv_path, custom_venv_base)
    return _create_venv


@pytest.fixture(scope='class')
def shared_custom_venvs(request, venv_path, is_docker, is_traditional_cluster_class):
    """Create custom venvs to be shared by whole class and tear down after.

       For classes using this fixture, provide a list of dictionaries that
       define the venvs to be created like this:

       Example:

       CUSTOM_VENVS = [
           {
           'name': 'python2_ansible23',
           'packages': 'psutil ansible==2.3',
           'python_interpreter': 'python2'
           },
           {
           'name': 'python2_ansibledevel',
           'packages': 'psutil git+https://github.com/ansible/ansible.git',
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
        # If we set the venv_group in fixture_args, override the defaults
        limit = fixture_args.kwargs.get('venv_group', None)
        if not limit:
            limit = 'instance_group_ordinary_instances' if is_traditional_cluster_class else 'tower'
            if is_docker:
                limit = 'tower'

        if 'venvs' not in fixture_args.kwargs.keys():
            pytest.fail('''
            Must provide "venvs" to create in fixture_args!
            See doc string of this fixture for more details on usage.
            ''')
        else:
            if limit == 'local' and is_docker:
                return venv_paths

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
                       inv_path,
                       ]
                teardown_playbook_args = [
                       venv_name,
                       limit,
                       use_python,
                       is_docker,
                       inv_path,
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
                        'Failed to create {} with packages {} using python interpreter {}:\n\n{}'.format(
                            venv_name, packages, use_python, e
                            )
                        )
        return venv_paths
