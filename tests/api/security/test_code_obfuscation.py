import pytest

from tests.api import APITest


@pytest.mark.usefixtures(
    'skip_if_openshift',
    'authtoken',
    'install_enterprise_license_unlimited',
)
class TestTowerLicense(APITest):

    def test_tower_license_source_is_hidden(self, ansible_runner):
        result = ansible_runner.shell(
            """echo "import inspect, tower_license; print(inspect.getsourcelines(tower_license.TowerLicense))" | awx-manage shell"""  # noqa
        ).values()[0]
        assert result['rc'] == 1
        assert 'could not get source code' in result['stderr']
