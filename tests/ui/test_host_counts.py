import pytest


pytestmark = [pytest.mark.ui]


@pytest.fixture(scope='module')
def hosts(api_v1, inventory):
    host_objs = [api_v1.hosts.create(inventory=inventory) for _ in xrange(5)]
    yield host_objs
    for obj in host_objs:
        obj.silent_cleanup()


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3135')
def test_host_counts_match(v1, ui, hosts):
    # get number of hosts reported by configuration endpoint
    config_hosts = v1.config.get().license_info.current_instances
    # get number of hosts reported by dashboard
    dashboard_hosts = ui.dashboard.find_count_button('hosts').count
    # get number of hosts reported by license page
    license_hosts = int(ui.license.get().hosts_used.text)
    # ensure reported host counts match
    assert config_hosts == dashboard_hosts == license_hosts
