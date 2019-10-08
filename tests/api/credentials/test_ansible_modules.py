import os

from awxkit import exceptions as exc
from awxkit.utils import suppress
import pytest
import fauxfactory

from tests.api import APITest


@pytest.mark.usefixtures('authtoken')
class TestGCECredentials(APITest):

    def test_gce_playbook_module(self, factories, gce_credential, ansible_venv_path):
        host = factories.host()
        jt = factories.job_template(
            inventory=host.ds.inventory,
            playbook='cloud_modules/gce.yml',
            verbosity=2,
            extra_vars={'state': 'absent', 'ansible_python_interpreter': os.path.join(ansible_venv_path, 'bin/python')}
        )
        with suppress(exc.NoContent):
            jt.related.credentials.post(
                {'id': gce_credential.id, 'associate': True}
            )
        job = jt.launch().wait_until_completed()
        job.assert_successful()

    def test_gce_playbook_module_via_collection(self, factories, gce_credential, ansible_venv_path):
        project = factories.project(
            name='Project with google.cloud collection requirement - %s' % fauxfactory.gen_utf8(),
            scm_type='git',
            scm_refspec='refs/pull/81/head:refs/remotes/origin/pull/81/head',
            scm_branch='pull/81/head'
        )
        host = factories.host()
        jt = factories.job_template(
            name='Job Template that runs google.cloud from collection - %s' % fauxfactory.gen_utf8(),
            project=project,
            inventory=host.ds.inventory,
            playbook='cloud_modules/gce.yml',
            verbosity=2,
            extra_vars={'state': 'absent', 'ansible_python_interpreter': os.path.join(ansible_venv_path, 'bin/python')}
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
