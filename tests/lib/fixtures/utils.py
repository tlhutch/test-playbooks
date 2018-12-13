from base64 import b64decode
import os
import gc
import logging
import fauxfactory
import pytest

from pytest_ansible.fixtures import ansible_facts as uncalled_ansible_facts


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
    """Returns the dump of Tower's Postgres DB as a string.
    It may consume a lot of memory if the db is big. Thus we should mark all tests using this fixture with:
    @pytest.mark.mp_group(group="get_pg_dump", strategy="serial")
    """

    def _pg_dump():
        # Run full garbage collection to release memory
        gc.collect()
        request.addfinalizer(gc.collect)

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
        # Look up host by name
        host = manager.get_host(host_name)
        # .. if no host found, attempt to find by ansible_host
        if not host:
            hosts = [h for h in manager.get_hosts() if h.vars.get('ansible_host', '') == host_name]
            if not hosts:
                raise Exception("Could not find host '{}'".format(host_name))
            host = hosts.pop()
        return host.get_vars()

    return gimme_hostvars


@pytest.fixture(scope='class')
def hosts_in_group(modified_ansible_adhoc):
    """Returns a generator that takes group name of a group in the inventory
    file and returns a list of instance hostnames in that group
    """
    manager = modified_ansible_adhoc().options['inventory_manager']

    def gimme_hosts(group_name, return_hostnames=False):
        """
        return_hostnames: return hostname instead of ansible_host
        (default behavior is to return ansible_host, if present)
        """
        group = manager.groups.get(group_name)
        if group is None:
            return []

        addresses = []
        for host in group.get_hosts():
            ansible_host = host.vars.get('ansible_host', '')

            if return_hostnames:
                address = host.name
            elif ansible_host:
                address = ansible_host
            else:
                address = host.name
            addresses.append(address)
        return addresses

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
    if request.node.get_closest_marker('skip_docker') and is_docker:
        pytest.skip(docker_skip_msg)


@pytest.fixture
def skip_if_fips_enabled(is_fips_enabled):
    if is_fips_enabled:
        pytest.skip('Cannot run on a FIPS enabled platform')


@pytest.fixture
def is_fips_enabled(is_docker, ansible_module):
    if is_docker:
        return False
    ansible_facts = uncalled_ansible_facts(ansible_module)
    return True in [dict(facts)['ansible_facts']['ansible_fips'] for host, facts in ansible_facts.contacted.iteritems()]
