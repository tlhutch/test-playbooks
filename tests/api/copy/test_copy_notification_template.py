from fauxfactory import gen_utf8
from awxkit.api.pages.notification_templates import notification_types
import pytest

from tests.api import APITest
from tests.lib.helpers.copy_utils import check_fields


@pytest.mark.usefixtures('authtoken')
class Test_Copy_Notification_Template(APITest):

    identical_fields = ['type', 'description', 'organization', 'notification_type', 'notification_configuration']
    unequal_fields = ['id', 'created', 'modified']

    @pytest.mark.parametrize('notification_type', notification_types)
    def test_copy_normal(self, factories, copy_with_teardown, notification_type):
        if notification_type in ('grafana', 'rocketchat'):
            pytest.skip('Do not currently have test support for {}'.format(notification_type))
        if notification_type == 'webhook':
            headers = {gen_utf8(): gen_utf8(), gen_utf8(): gen_utf8()}
            notification_template = factories.notification_template(notification_type=notification_type,
                                                                          headers=headers)
        else:
            notification_template = factories.notification_template(notification_type=notification_type)

        new_notification_template = copy_with_teardown(notification_template)
        check_fields(notification_template, new_notification_template, self.identical_fields, self.unequal_fields)
