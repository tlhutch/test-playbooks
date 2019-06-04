from fauxfactory import gen_boolean, gen_integer
import pytest

from tests.api import APITest
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_Project(APITest):

    identical_fields = ['type', 'description', 'organization', 'scm_type', 'scm_url', 'scm_branch', 'scm_clean',
                        'scm_delete_on_update', 'scm_update_on_launch', 'scm_update_cache_timeout', 'custom_virtualenv',
                        'timeout']
    unequal_fields = ['id', 'created', 'modified', 'local_path']

    @pytest.mark.parametrize("wait", [True, False], ids=['wait', 'nowait'])
    def test_copy_normal(self, factories, copy_with_teardown, wait):
        v2_project = factories.project(wait=wait)
        new_project = copy_with_teardown(v2_project)
        check_fields(v2_project, new_project, self.identical_fields, self.unequal_fields)
        assert new_project.related.current_update

    @pytest.mark.yolo
    def test_copy_project_with_non_default_values(self, factories, copy_with_teardown):
        max_int32 = 1 << 31 - 1
        v2_project = factories.project(
            scm_branch='master', scm_clean=gen_boolean(), scm_delete_on_update=gen_boolean(),
            scm_update_on_launch=gen_boolean(),
            scm_update_cache_timeout=gen_integer(min_value=-1, max_value=max_int32),
            timeout=gen_integer(min_value=-1, max_value=max_int32),
            wait=False)
        new_project = copy_with_teardown(v2_project)
        check_fields(v2_project, new_project, self.identical_fields, self.unequal_fields)
        assert new_project.related.current_update
