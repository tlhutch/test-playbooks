import pytest
import towerkit.exceptions as exc

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCopying(APITest):

    @pytest.mark.parametrize('obj', [
        'job_template',
        'project',
        'inventory',
        'inventory_script',
        'credential',
        'workflow_job_template',
        'notification_template',
    ])
    def test_v1_copy_is_not_allowed(self, factories, v1, obj):
        assert 'copy' in getattr(factories, 'v2_{}'.format(obj))().related
        x = getattr(factories, obj)()
        assert 'copy' not in x.related
        with pytest.raises(exc.NotFound, message='Action only possible starting with v2 API.'):
            v1.walk(x.url + 'copy/').post({'name': 'Some Copy'})
