
from towerkit.config import config

import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Ansible_Tower_Modules(APITest):

    def test_all_tower_modules(self, v2, factories, admin_user):
        proj = v2.projects.create(scm_type='git',
                                  scm_url='http://github.com/chrismeyersfsu/tower_modules',
                                  scm_branch='master',
                                  scm_clean=False,
                                  scm_delete_on_update=False,
                                  scm_update_on_launch=False)

        cred = factories.v2_credential(kind='tower', username=admin_user.username,
                                       password=admin_user.password, host=config.base_url)
        jt = factories.v2_job_template(project=proj, playbook='tests/main.yml')
        jt.add_credential(cred)
        job = jt.launch().wait_until_completed()

        job.assert_successful()
