import pprint

import pytest

from tests.api import APITest


@pytest.mark.usefixtures('skip_if_openshift', 'authtoken')
class TestTowerLicense(APITest):

    def test_tower_license_source_is_hidden(self, modified_ansible_adhoc):
        result = modified_ansible_adhoc().tower.shell(
            """echo "import inspect, tower_license; print(inspect.getsourcelines(tower_license.TowerLicense))" | awx-manage shell"""  # noqa
        ).values()[0]
        assert result['rc'] == 1, pprint.pformat(result)
        assert 'could not get source code' in result['stderr']
