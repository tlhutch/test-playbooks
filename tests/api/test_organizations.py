'''
# 1) Verify users with unicode names and passwords
# 2) Verify credentials, owned by the user, are removed upon DELETE
'''

import json
import pytest
import common.utils
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

    # FIXME coming soon
#    def test_duplicate(self, api_users_pg, some_user):
#        '''Verify that usernames are unique'''
#        payload = dict(username=some_user.username,
#                       first_name="Another Joe (%s)" % common.utils.random_unicode(),
#                       last_name="User (%s)" % common.utils.random_unicode(),
#                       email="org_user_%s@example.com" % common.utils.random_ascii(),
#                       password=common.utils.random_unicode())
#        with pytest.raises(common.exceptions.Duplicate_Exception):
#            api_users_pg.post(payload)

    def test_cascade_delete(self, api_organizations_pg, organization, inventory_script):
        '''
        Verify that a inventory_scripts are deleted when the organization is
        deleted.

        TODO - this should test for other related fields.
        '''

        # Delete the organization
        organization.delete()

        # assert the organization was deleted
        matches = api_organizations_pg.get(id=organization.id)
        assert matches.count == 0, "An organization was deleted, but is still visible from the /api/v1/organizations/ endpoint"

        # assert the related inventory_scripts were deleted
        with pytest.raises(common.exceptions.NotFound_Exception):
            inventory_script.get()
