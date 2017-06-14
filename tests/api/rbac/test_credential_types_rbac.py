from towerkit.utils import credential_type_kinds
from towerkit import exceptions as exc
import pytest

from tests.api import Base_Api_Test


@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class TestCredentialTypesRBAC(Base_Api_Test):

    def test_non_superuser_cannot_create_credential_type(self, factories, non_superuser):
        with self.current_user(non_superuser):
            for kind in credential_type_kinds:
                with pytest.raises(exc.Forbidden):
                    factories.credential_type(kind=kind)
