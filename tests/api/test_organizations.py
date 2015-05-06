import pytest
import common.exceptions
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.destructive
@pytest.mark.skip_selenium
class Test_Organizations(Base_Api_Test):
    '''
    Verify the /users endpoint displays the expected information based on the current user
    '''
    pytestmark = pytest.mark.usefixtures('authtoken')

    # TODO - test_post_as_superuser
    # TODO - test_patch_as_superuser
    # TODO - test_put_as_superuser

    # TODO - test_post_as_non_superuser
    # TODO - test_put_as_non_superuser
    # TODO - test_patch_as_non_superuser

    def test_duplicate(self, api_organizations_pg, organization):
        '''
        Verify that organization names are unique.
        '''
        payload = dict(name=organization.name)
        with pytest.raises(common.exceptions.Duplicate_Exception):
            api_organizations_pg.post(payload)

    def test_delete(self, api_organizations_pg, organization):
        '''
        Verify that deleting an organization actually works.
        '''

        # Delete the organization
        organization.delete()

        # assert the organization was deleted
        matches = api_organizations_pg.get(id=organization.id)
        assert matches.count == 0, "An organization was deleted, but is still visible from the /api/v1/organizations/ endpoint"
