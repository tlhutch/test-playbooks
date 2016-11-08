import logging

import towerkit.exceptions
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.mark.api
@pytest.mark.skip_selenium
class TestActivityStream(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license')

    def test_limited_view_of_unprivileged_user(self, factories, api_activity_stream_pg, user_password):
        """Confirms that unprivileged users only see their creation details in activity stream"""
        activity = api_activity_stream_pg
        user = factories.user(organization=factories.organization())

        # generate activity that user shouldn't have access to in activity stream
        for _ in range(3):
            org = factories.organization()
            for _ in range(5):
                factories.credential(user=factories.user(organization=org), organization=None)

        with self.current_user(user.username, user_password):
            activity.get()

        # confirm that only user creation events for user in question are shown
        for result in activity.results:
            try:
                assert result.summary_fields.user[0].username == user.username
            except AttributeError:
                # roll JSON_Wrapper Attribute errors in here too
                raise(Exception("Unprivileged user has access to unexpected activity stream content."))

    def test_inventory_id_in_group_activity_stream(self, factories):
        """Confirms that inventory_id is included in the group summary_fields for all non-delete operations"""
        inventory = factories.inventory()
        group = factories.group(inventory=inventory)
        host = factories.host(inventory=inventory)

        group.name = "UpdatedGroupName"
        with pytest.raises(towerkit.exceptions.NoContent):
            group.get_related('hosts').post(dict(associate=True, id=host.id))
        with pytest.raises(towerkit.exceptions.NoContent):
            group.get_related('hosts').post(dict(disassociate=True, id=host.id))

        operations = ['create', 'update', 'associate', 'disassociate']

        activity = group.get_related('activity_stream')
        for result in activity.results:
            assert 'inventory_id' in result.summary_fields.group[0]
            operations.remove(result.operation)

        assert(not operations
               ), "Failed to find activity for all operations.  Missing: {}".format(operations)
