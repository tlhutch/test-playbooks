import pytest

import towerkit.exceptions
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Notifications_RBAC(Base_Api_Test):

    def test_notification_read_as_unprivileged_user(self, email_notification_template, unprivileged_user):
        """Test that unprivileged users cannot read notifications."""
        notification_pg = email_notification_template.test().wait_until_completed()

        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                notification_pg.get()

    def test_notification_read_as_org_admin(self, factories, org_admin):
        """Test that org_admins can read notifications."""
        organization = org_admin.related.organizations.get().results.pop()
        notification_template = factories.notification_template(organization=organization)
        notification_pg = notification_template.test().wait_until_completed()

        with self.current_user(username=org_admin.username, password=org_admin.password):
            notification_pg.get()

    def test_notification_test_as_unprivileged_user(self, email_notification_template, unprivileged_user):
        """Confirms that unprivileged users cannot test notifications."""
        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.test().wait_until_completed()

    def test_notification_test_as_another_org_admin(self, email_notification_template, another_org_admin):
        """Confirms that admins of other orgs cannot test notifications outside their organization"""
        with self.current_user(username=another_org_admin.username, password=another_org_admin.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.test().wait_until_completed()
