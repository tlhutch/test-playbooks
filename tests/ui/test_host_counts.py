import pytest

from qe.api import ApiV1
from qe.ui.models import License


pytestmark = [pytest.mark.ui, pytest.mark.nondestructive]


@pytest.fixture
def multiple_hosts(authtoken, install_enterprise_license, factories):
    return [factories.host() for _ in xrange(5)]


@pytest.mark.github('https://github.com/ansible/ansible-tower/issues/3135')
def test_host_counts_match(multiple_hosts, ui_dashboard, selenium, base_url):
    v1 = ApiV1()
    v1.load_default_authtoken()
    # get number of hosts reported by configuration endpoint
    config_hosts = v1.get().config.get().license_info.current_instances
    # get number of hosts reported by dashboard
    dashboard_hosts = ui_dashboard.find_count_button('hosts').count
    # get number of hosts reported by license page
    license_page = License(selenium, base_url).open()
    license_hosts = int(license_page.hosts_used.text)
    # ensure reported host counts match
    assert config_hosts == dashboard_hosts == license_hosts
