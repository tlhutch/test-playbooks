import pytest

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    check_user_capabilities,
    get_nt_endpoints,
    set_read_role
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.skip_selenium
class Test_Notification_Template_RBAC(Base_Api_Test):

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    def test_notification_template_create_as_unprivileged_user(self, factories, unprivileged_user):
        """Tests that unprivileged users may not create notification templates."""
        # test notification template create as unprivileged user
        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.notification_template()

    def test_notification_template_create_as_org_admin(self, factories, org_admin):
        """Tests that org_admins may create notification templates."""
        # test notification template create as org_admin
        organization = org_admin.related.organizations.get().results.pop()
        with self.current_user(username=org_admin.username, password=org_admin.password):
            factories.notification_template(organization=organization)

    def test_notification_template_associate_as_unprivileged_user(self, email_notification_template, notifiable_resource,
                                                                  unprivileged_user, user_password):
        """Tests that unprivileged users may not associate a NT with a notifiable resource."""
        # store our future test endpoints
        endpoints = get_nt_endpoints(notifiable_resource)

        # give our test user 'read' permissions
        set_read_role(unprivileged_user, notifiable_resource)

        # test notification template associate as unprivileged user
        payload = dict(id=email_notification_template.id)
        with self.current_user(username=unprivileged_user.username, password=user_password):
            for endpoint in endpoints:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    endpoint.post(payload)

    def test_notification_template_associate_as_org_admin(self, factories, notifiable_resource, org_admin, user_password):
        """Tests that org_admins may associate a NT with a notifiable resource."""
        # store our future test endpoints
        endpoints = get_nt_endpoints(notifiable_resource)

        organization = org_admin.related.organizations.get().results.pop()
        notification_template = factories.notification_template(organization=organization)

        # test notification template associate as org_admin
        payload = dict(id=notification_template.id)
        with self.current_user(username=org_admin.username, password=user_password):
            for endpoint in endpoints:
                with pytest.raises(towerkit.exceptions.NoContent):
                    endpoint.post(payload)

    def test_notification_template_read_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        """Tests that unprivileged users cannot read NT endpoints."""
        # assert that we cannot access api/v1/notification_templates
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.get()

    def test_notification_template_read_as_org_admin(self, factories, org_admin, user_password):
        """Tests that org_admins can read NT endpoints."""
        # assert that we can access api/v1/notification_templates

        organization = org_admin.related.organizations.get().results.pop()
        notification_template = factories.notification_template(organization=organization)
        with self.current_user(username=org_admin.username, password=user_password):
            notification_template.get()

    def test_notification_template_edit_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        """Tests that unprivileged users cannot edit NTs."""
        # assert that put/patch is forbidden
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.patch()

    def test_notification_template_edit_as_org_admin(self, factories, org_admin, user_password):
        """Tests that org_admins can edit NTs."""
        # assert that put/patch is accepted
        organization = org_admin.related.organizations.get().results.pop()
        notification_template = factories.notification_template(organization=organization)
        with self.current_user(username=org_admin.username, password=user_password):
            notification_template.put()
            notification_template.patch()

    def test_notification_template_delete_as_unprivileged_user(self, email_notification_template, unprivileged_user, user_password):
        """Tests that unprivileged_users cannot delete NTs."""
        # assert that delete is forbidden
        with self.current_user(username=unprivileged_user.username, password=user_password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.delete()

    def test_notification_template_delete_as_org_admin(self, factories, org_admin, user_password):
        """Tests that org_admins can delete NTs."""
        # assert that delete is accepted
        organization = org_admin.related.organizations.get().results.pop()
        notification_template = factories.notification_template(organization=organization)
        with self.current_user(username=org_admin.username, password=user_password):
            notification_template.delete()

    def test_user_capabilities_as_superuser(self, email_notification_template, api_notification_templates_pg):
        """Tests NT 'user_capabilities' as superuser."""
        check_user_capabilities(email_notification_template.get(), "superuser")
        check_user_capabilities(api_notification_templates_pg.get(id=email_notification_template.id).results.pop(), "superuser")

    def test_user_capabilities_as_org_admin(self, factories, org_admin, user_password, api_notification_templates_pg):
        """Tests NT 'user_capabilities' as an org_admin."""
        organization = org_admin.related.organizations.get().results.pop()
        notification_template = factories.notification_template(organization=organization)
        with self.current_user(username=org_admin.username, password=user_password):
            check_user_capabilities(notification_template.get(), "org_admin")
            check_user_capabilities(api_notification_templates_pg.get(id=notification_template.id).results.pop(), "org_admin")
