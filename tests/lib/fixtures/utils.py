from base64 import b64decode
import os
import logging
from pkg_resources import parse_version

from ansible import __version__ as ansible_version

import fauxfactory
import pytest


@pytest.fixture
def subrequest(request):
    # https://github.com/pytest-dev/pytest/issues/2495
    # To ensure that teardowns occur roughly in registered order
    # do not use the request fixture directly as all its finalizer calls
    # will occur in same block
    return request


@pytest.fixture(scope='class')
def class_subrequest(request):
    return request


@pytest.fixture
def get_pg_dump(request, ansible_runner, skip_docker, hostvars_for_host):

    def _pg_dump():
        inv_path = os.environ.get('TQA_INVENTORY_FILE_PATH', '/tmp/setup/inventory')
        dump_filename = 'pg_{}.txt'.format(fauxfactory.gen_alphanumeric())
        contacted = ansible_runner.shell("""PGPASSWORD=`grep {} -e "pg_password=.*" """
                                         """| sed \'s/pg_password="//\' | sed \'s/"//\'` """
                                         """pg_dump -U awx -d awx -f {} -w""".format(inv_path, dump_filename))
        for res in contacted.values():
            assert res.get('changed') and not res.get('failed')

        user = ansible_runner.options['user']
        if not user:
            host_pattern = ansible_runner.options['host_pattern']
            this_host_vars = hostvars_for_host(host_pattern)
            user = this_host_vars['ansible_user']
        pg_dump_path = '/home/{0}/{1}'.format(user, dump_filename)
        request.addfinalizer(lambda: ansible_runner.file(path=pg_dump_path, state='absent'))

        # Don't log the dumped db.
        pa_logger = logging.getLogger('pytest_ansible')
        prev_level = pa_logger.level
        pa_logger.setLevel('INFO')
        restored = [False]

        def restore_log_level():
            if not restored[0]:
                pa_logger.setLevel(prev_level)
                restored[0] = True

        request.addfinalizer(restore_log_level)

        contacted = ansible_runner.slurp(src=pg_dump_path)
        restore_log_level()

        res = contacted.values().pop()

        assert not res.get('failed') and res['content']
        return b64decode(res['content'])

    return _pg_dump


@pytest.fixture(scope='class')
def modified_ansible_adhoc(request):
    # HACK: re-implement ansible_adhoc fixture from pytest-ansible
    # becuase that is the only way to do this class-scoped
    plugin = request.config.pluginmanager.getplugin("ansible")

    def init_host_mgr(**kwargs):
        return plugin.initialize(request.config, request, **kwargs)
    return init_host_mgr


@pytest.fixture(scope='class')
def hostvars_for_host(modified_ansible_adhoc):
    """Returns a generator that takes a host name in the inventory file
    and returns variables for that host
    """
    manager = modified_ansible_adhoc().options['inventory_manager']

    def gimme_hostvars(host_name):
        if parse_version(ansible_version) < parse_version('2.3'):
            raise RuntimeError('Local version of Ansible is so old {}'.format(ansible_version))
        else:
            return manager.get_host(host_name).get_vars()

    return gimme_hostvars


@pytest.fixture(scope='class')
def hosts_in_group(modified_ansible_adhoc):
    """Returns a generator that takes group name of a group in the inventory
    file and returns a list of instance hostnames in that group
    """
    manager = modified_ansible_adhoc().options['inventory_manager']

    def gimme_hosts(group_name):
        if parse_version(ansible_version) < parse_version('2.3'):
            raise RuntimeError('Local version of Ansible is so old {}'.format(ansible_version))
        elif parse_version(ansible_version) < parse_version('2.4'):
            groups_dict = manager.get_group_dict() if hasattr(manager, 'get_group_dict') else manager.get_groups_dict()
            return groups_dict.get(group_name)
        else:
            return [host.name for host in manager.groups[group_name].get_hosts()]

    return gimme_hosts


@pytest.fixture(scope='class')
def is_docker(hosts_in_group, hostvars_for_host):
    try:
        tower_hosts = hosts_in_group('tower')
        return hostvars_for_host(tower_hosts[0]).get('ansible_connection') == 'docker'
    except (TypeError, IndexError):
        return False


docker_skip_msg = "Test doesn't support dev container"


@pytest.fixture
def skip_docker(is_docker):
    if is_docker:
        pytest.skip(docker_skip_msg)


@pytest.fixture(autouse=True)
def _skip_docker(request, is_docker):
    if request.node.get_marker('skip_docker') and is_docker:
        pytest.skip(docker_skip_msg)
