from towerkit import exceptions as exc
from towerkit.utils import suppress
import pytest

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestGCECredentials(APITest):

    def test_gce_playbook_module(self, factories, gce_credential, venv_path):
        host = factories.host()
        jt = factories.job_template(
            inventory=host.ds.inventory,
            playbook='cloud_modules/gce.yml',
            verbosity=2,
            extra_vars={'state': 'absent', 'ansible_python_interpreter': '{}/bin/python'.format(venv_path())}
        )
        with suppress(exc.NoContent):
            jt.related.credentials.post(
                {'id': gce_credential.id, 'associate': True}
            )
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    def test_gce_inventory_sync(self, factories, gce_credential):
        inv_source = factories.inventory_source(source='gce', credential=gce_credential, verbosity=2)
        inv_update = inv_source.update().wait_until_completed()
        assert inv_update.status == 'successful'

        # we currently host zuul workers in GCE, so at least one should show up here
        assert 'Host "zuul-' in inv_update.result_stdout
