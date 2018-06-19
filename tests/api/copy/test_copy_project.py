from fauxfactory import gen_boolean, gen_integer
import pytest

from tests.api import Base_Api_Test
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.api
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Copy_Project(Base_Api_Test):

    identical_fields = ['type', 'description', 'organization', 'scm_type', 'scm_url', 'scm_branch', 'scm_clean',
                        'scm_delete_on_update', 'scm_update_on_launch', 'scm_update_cache_timeout', 'custom_virtualenv',
                        'timeout']
    unequal_fields = ['id', 'created', 'modified', 'local_path']

    @pytest.mark.parametrize("wait", [True, False], ids=['wait', 'nowait'])
    def test_copy_normal(self, factories, copy_with_teardown, wait):
        v2_project = factories.v2_project(wait=wait)
        new_project = copy_with_teardown(v2_project)
        check_fields(v2_project, new_project, self.identical_fields, self.unequal_fields)
        assert new_project.related.current_update

    def test_copy_project_with_non_default_values(self, factories, copy_with_teardown):
        min_int32 = -1 << 31
        max_int32 = 1 << 31 - 1
        v2_project = factories.v2_project(
            scm_branch='master', scm_clean=gen_boolean(), scm_delete_on_update=gen_boolean(),
            scm_update_on_launch=gen_boolean(),
            scm_update_cache_timeout=gen_integer(min_value=min_int32, max_value=max_int32),
            timeout=gen_integer(min_value=min_int32, max_value=max_int32),
            wait=False)
        new_project = copy_with_teardown(v2_project)
        check_fields(v2_project, new_project, self.identical_fields, self.unequal_fields)
        assert new_project.related.current_update

    def test_copy_with_credential_permission(self, factories, copy_with_teardown):
        credendial = factories.v2_credential(kind='scm')
        v2_project = factories.v2_project(credential=credendial, wait=False)
        new_project = copy_with_teardown(v2_project)

        check_fields(v2_project, new_project, self.identical_fields, self.unequal_fields)
        assert new_project.related.current_update
        assert new_project.credential == v2_project.credential

    def test_copy_without_credential_permission(self, factories, copy_with_teardown, set_test_roles):
        credendial = factories.v2_credential(kind='scm')
        organization = factories.v2_organization()
        v2_project = factories.v2_project(credential=credendial, organization=organization, wait=False)
        user = factories.user()
        set_test_roles(user, organization, 'user', 'admin')

        with self.current_user(user):
            new_project = copy_with_teardown(v2_project)

            check_fields(v2_project, new_project, self.identical_fields, self.unequal_fields)
            assert new_project.related.current_update
            assert not new_project.credential
