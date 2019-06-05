
from towerkit.config import config

import pytest
import json

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Ansible_Tower_Modules(APITest):

    """
    Ansible modules that interact with Tower live in an Ansible Collection.
    Along side those modules live playbooks that test the modules in the
    collection.
    This test invokes those test that live along side the collection.
    """
    @pytest.mark.parametrize('tower_module',
                             ['common',
                              'credential', 'credential_type',
                              'group', 'host', 'inventory', 'inventory_source',
                              'job_cancel', 'job_launch', 'job_list', 'job_template', 'job_wait',
                              'label',
                              'notification',
                              'project',
                              'receive', 'send',
                              'role',
                              'settings',
                              'team', 'user',
                              'workflow_template',
                             ])
    def test_ansible_tower_module(self, v2, factories, admin_user, tower_module):
        proj = factories.v2_project(scm_type='git',
                                    scm_url='http://github.com/chrismeyersfsu/ansible-playbooks',
                                    scm_branch='tower_modules',
                                    scm_clean=False,
                                    scm_delete_on_update=False,
                                    scm_update_on_launch=False)

        cred = factories.v2_credential(kind='tower', username=admin_user.username,
                                       password=admin_user.password, host=config.base_url)
        extra_vars = {
            'tower_module_under_test': tower_module
        }
        jt = factories.v2_job_template(project=proj, playbook='tower_modules/wrapper.yml',
                                       extra_vars=json.dumps(extra_vars))
        jt.add_credential(cred)
        job = jt.launch().wait_until_completed()

        job.assert_successful()
