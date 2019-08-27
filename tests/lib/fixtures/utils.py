from base64 import b64decode
import os
import gc
import logging
import fauxfactory
import pytest
import socket


# Session scoped fixtures
#

@pytest.fixture(scope='session')
def session_ansible_adhoc(request):
    plugin = request.config.pluginmanager.getplugin("ansible")

    def init_host_mgr(**kwargs):
        return plugin.initialize(request.config, request, **kwargs)
    return init_host_mgr


@pytest.fixture(scope='session')
def session_ansible_module(session_ansible_adhoc):
    """Return a subclass of BaseModuleDispatcher."""
    host_mgr = session_ansible_adhoc()
    return getattr(host_mgr, host_mgr.options['host_pattern'])


@pytest.fixture(scope='session')
def session_ansible_facts(session_ansible_module):
    """Return ansible_facts dictionary."""
    return session_ansible_module.setup()


@pytest.fixture(scope='session')
def session_ansible_python(session_hosts_in_group, session_hostvars_for_host, session_ansible_facts):
    """Return the ansible_python for the first tower host on the inventory.

    :raises: IndexError in case there is no host on the tower group or was not
        able to fetch the ansible_python fact for the first tower host.
    """
    tower_hosts = [
        session_hostvars_for_host(host)['inventory_hostname']
        for host in session_hosts_in_group('tower')
    ]
    for host, facts in session_ansible_facts.items():
        if host in tower_hosts:
            break
    return facts['ansible_facts']['ansible_python']


@pytest.fixture(scope='session')
def session_hostvars_for_host(session_ansible_adhoc):
    """Returns a generator that takes a host name in the inventory file
    and returns variables for that host
    """
    manager = session_ansible_adhoc().options['inventory_manager']

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


@pytest.fixture(scope='session')
def session_hosts_in_group(session_ansible_adhoc):
    """Returns a generator that takes group name of a group in the inventory
    file and returns a list of instance hostnames in that group
    """
    manager = session_ansible_adhoc().options['inventory_manager']

    def gimme_hosts(group_name, return_hostnames=False, return_map=False):
        """
        Default behavior is to return list of ansible_host, if present

        :param return_hostnames: Boolean, return list of hostnames instead

        :param return_map: Boolean, return a mapping between hostname and
            ansible_host if it is available. Otherwise just a map of the
            hostname to the hostname to keep tests sane, because in this case
            that is all the info we have and just have to run with it.
        """
        group = manager.groups.get(group_name)
        if group is None:
            return []
        addresses = []
        if return_map:
            addresses = {}
        for host in group.get_hosts():
            ansible_host = host.vars.get('ansible_host', '')
            if return_map:
                addresses[host.name] = ansible_host if ansible_host else host.name
                continue
            elif return_hostnames:
                address = host.name
            elif ansible_host:
                address = ansible_host
            else:
                address = host.name
            addresses.append(address)
        return addresses

    return gimme_hosts


@pytest.fixture(scope='session')
def is_docker(session_hosts_in_group, session_hostvars_for_host):
    try:
        tower_hosts = session_hosts_in_group('tower')
        return session_hostvars_for_host(tower_hosts[0]).get('ansible_connection') == 'docker'
    except (TypeError, IndexError):
        return False


@pytest.fixture(scope='session')
def ansible_venv_path(v2_session):
    venvs = v2_session.config.get().custom_virtualenvs
    for v in venvs:
        if 'venv/ansible/' in v:
            return v


@pytest.fixture(scope='session')
def is_dev_container(is_docker, ansible_venv_path):
    return is_docker and '/venv/ansible/' == ansible_venv_path


@pytest.fixture(scope='session')
def is_fips_enabled(is_docker, session_ansible_facts):
    if is_docker:
        return False
    return True in [dict(facts)['ansible_facts']['ansible_fips'] for host, facts in session_ansible_facts.contacted.items()]


@pytest.fixture(scope='session')
def is_cluster(is_traditional_cluster, is_openshift_cluster):
    return is_traditional_cluster or is_openshift_cluster


@pytest.fixture(scope='session')
def is_traditional_cluster(v2_session, is_docker):
    return v2_session.ping.get()['ha'] and not is_docker


@pytest.fixture(scope='session')
def is_vpn():
    try:
        socket.gethostbyname('subscription.rhsm.stage.redhat.com')
        return True
    except socket.error:
        return False


@pytest.fixture(scope='session')
def skip_if_not_vpn(is_vpn):
    if not is_vpn:
        pytest.skip("Test must be run on the VPN")


@pytest.fixture(scope='session')
def is_openshift_cluster(v2_session, is_docker):
    return v2_session.ping.get()['ha'] and is_docker


@pytest.fixture(scope='session')
def skip_docker(is_docker):
    if is_docker:
        pytest.skip("Test doesn't support dev container")


@pytest.fixture(scope='session')
def skip_if_fips_enabled(is_fips_enabled):
    if is_fips_enabled:
        pytest.skip('Cannot run on a FIPS enabled platform')


@pytest.fixture(scope='session')
def skip_if_not_traditional_cluster(is_traditional_cluster):
    if not is_traditional_cluster:
        pytest.skip('Cannot run on an non traditional cluster install')


@pytest.fixture(scope='session')
def skip_if_openshift(is_openshift_cluster):
    if is_openshift_cluster:
        pytest.skip('Cannot run on an OpenShift install')


@pytest.fixture(scope='session')
def skip_if_not_openshift(is_openshift_cluster):
    if not is_openshift_cluster:
        pytest.skip('Cannot run on an non-OpenShift install')


@pytest.fixture(scope='session')
def skip_if_not_cluster(is_cluster):
    if not is_cluster:
        pytest.skip('Cannot run on a non-cluster install')


@pytest.fixture(scope='session')
def skip_if_cluster(is_cluster):
    if is_cluster:
        pytest.skip('Cannot run on a cluster install')


@pytest.fixture(scope='session')
def skip_if_pre_ansible28(ansible_version_cmp):
    if ansible_version_cmp('2.8.0') < 0:
        pytest.skip('Cannot run with version of Ansible pre 2.8.0')


@pytest.fixture(scope='session')
def skip_if_pre_ansible29(ansible_version_cmp):
    if ansible_version_cmp('2.9.0') < 0:
        pytest.skip('Cannot run with version of Ansible pre 2.9.0')


# Class scoped fixtures
#

@pytest.fixture(scope='class')
def is_traditional_cluster_class(v2_class):
    return v2_class.ping.get()['ha'] and not is_docker


@pytest.fixture(scope='class')
def class_subrequest(request):
    return request


@pytest.fixture(scope='module')
def module_subrequest(request):
    return request


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

    def gimme_hosts(group_name, return_hostnames=False, return_map=False):
        """
        Default behavior is to return list of ansible_host, if present

        :param return_hostnames: Boolean, return list of hostnames instead

        :param return_map: Boolean, return a mapping between hostname and
            ansible_host if it is available. Otherwise just a map of the
            hostname to the hostname to keep tests sane, because in this case
            that is all the info we have and just have to run with it.
        """
        group = manager.groups.get(group_name)
        if group is None:
            return []
        addresses = []
        if return_map:
            addresses = {}
        for host in group.get_hosts():
            ansible_host = host.vars.get('ansible_host', '')
            if return_map:
                addresses[host.name] = ansible_host if ansible_host else host.name
                continue
            elif return_hostnames:
                address = host.name
            elif ansible_host:
                address = ansible_host
            else:
                address = host.name
            addresses.append(address)
        return addresses

    return gimme_hosts


@pytest.fixture(scope='class')
def inventory_hostname_map(modified_ansible_adhoc):
    manager = modified_ansible_adhoc().options['inventory_manager']
    group = manager.groups.get('all')

    mapping = []
    for host in group.get_hosts():
        ansible_host = host.vars.get('ansible_host', '')
        if not ansible_host:
            continue
        mapping.append((host.name, ansible_host))
    if not mapping:
        raise Exception('No hosts in inventory specify ansible_host')

    def get_alternate_hostname(host):
        # poor man's bidirectional map
        for pair in mapping:
            if host == pair[0]:
                return pair[1]
            if host == pair[1]:
                return pair[0]
        raise Exception('{} not found in hostname mapping'.format(host))
    return get_alternate_hostname


# Function scoped fixtures
#

@pytest.fixture
def subrequest(request):
    # https://github.com/pytest-dev/pytest/issues/2495
    # To ensure that teardowns occur roughly in registered order
    # do not use the request fixture directly as all its finalizer calls
    # will occur in same block
    return request


@pytest.fixture
def get_pg_dump(request, ansible_runner, skip_docker, hostvars_for_host):
    """Returns the dump of Tower's Postgres DB as a string.
    It may consume a lot of memory if the db is big. Thus we should mark all tests using this fixture with:
    @pytest.mark.serial
    """

    def _pg_dump():
        # Run full garbage collection to release memory
        gc.collect()
        request.addfinalizer(gc.collect)

        inv_path = os.environ.get('TQA_INVENTORY_FILE_PATH', '/tmp/setup/inventory')
        dump_filename = 'pg_{}.txt'.format(fauxfactory.gen_alphanumeric())

        contacted = ansible_runner.shell("""PGPASSWORD=`grep {} -e "pg_password=.*" """
                                         """| sed \'s/pg_password="//\' | sed \'s/"//\'` """
                                         """scl enable rh-postgresql10 'pg_dump -U awx -d awx -f {} -w'""".format(inv_path, dump_filename))
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

        res = list(contacted.values()).pop()

        assert not res.get('failed') and res['content']
        return b64decode(res['content']).decode()

    return _pg_dump


@pytest.fixture
def host_script():
    """Given N, this produces text which can be used in an inventory script
    that prints JSON output that defines an inventory with N hosts
    """
    def give_me_text(hosts=0, groups=0):
        return '\n'.join([
            "#!/usr/bin/env python",
            "import json",
            "data = {'_meta': {'hostvars': {}}}",
            "for i in range({}):".format(hosts),
            "   data.setdefault('ungrouped', []).append('Host-{}'.format(i))",
            "for i in range({}):".format(groups),
            "   data['Group-{}'.format(i)] = {'vars': {'foo': 'bar'}}",
            "print(json.dumps(data, indent=2))"
        ])
    return give_me_text
