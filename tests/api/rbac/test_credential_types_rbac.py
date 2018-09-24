from towerkit.utils import credential_type_kinds
from towerkit import exceptions as exc
import pytest

from tests.api import APITest


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCredentialTypesRBAC(APITest):

    def test_non_superuser_cannot_create_credential_type(self, factories, non_superuser):
        with self.current_user(non_superuser):
            for kind in credential_type_kinds:
                with pytest.raises(exc.Forbidden):
                    factories.credential_type(kind=kind)

    def test_non_superusers_can_see_credential_types(self, factories, v2, non_superuser):
        superuser_ct_count = v2.credential_types.get().count
        with self.current_user(non_superuser):
            for credential_type in v2.credential_types.get(page_size=200).results:
                credential_type.get()
            assert v2.credential_types.get().count == superuser_ct_count
