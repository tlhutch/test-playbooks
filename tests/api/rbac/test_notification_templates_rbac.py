import pytest

import towerkit.exceptions
from tests.lib.helpers.rbac_utils import (
    check_user_capabilities,
    get_nt_endpoints
)
from tests.api import Base_Api_Test


@pytest.mark.api
@pytest.mark.rbac
@pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')
class Test_Notification_Template_RBAC(Base_Api_Test):

    def set_read_role(self, user, notifiable_resource):
        if notifiable_resource.type == 'inventory_source':
            inventory = notifiable_resource.related.inventory.get()
            inventory.set_object_roles(user, 'read')
        else:
            notifiable_resource.set_object_roles(user, 'read')

    def test_notification_template_create_as_unprivileged_user(self, factories, unprivileged_user):
        """Tests that unprivileged users may not create notification templates."""
        organization = factories.organization()
        organization.set_object_roles(unprivileged_user, "read")

        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                factories.notification_template(organization=organization)

    def test_notification_template_create_as_org_admin(self, factories, organization, org_admin):
        """Tests that org_admins may create notification templates."""
        with self.current_user(username=org_admin.username, password=org_admin.password):
            factories.notification_template(organization=organization)

    def test_notification_template_associate_as_unprivileged_user(self, email_notification_template, notifiable_resource,
                                                                  unprivileged_user):
        """Tests that unprivileged users may not associate a NT with a notifiable resource."""
        endpoints = get_nt_endpoints(notifiable_resource)
        self.set_read_role(unprivileged_user, notifiable_resource)

        # test notification template associate as unprivileged user
        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            for endpoint in endpoints:
                with pytest.raises(towerkit.exceptions.Forbidden):
                    notifiable_resource.add_notification_template(email_notification_template, endpoint)

    def test_notification_template_associate_as_org_admin(self, factories, notifiable_resource, organization, org_admin):
        """Tests that org_admins may associate a NT with a notifiable resource."""
        endpoints = get_nt_endpoints(notifiable_resource)
        notification_template = factories.notification_template(organization=organization)

        # test notification template associate as org_admin
        with self.current_user(username=org_admin.username, password=org_admin.password):
            for endpoint in endpoints:
                notifiable_resource.add_notification_template(notification_template, endpoint)

    def test_notification_template_read_as_unprivileged_user(self, email_notification_template, unprivileged_user):
        """Tests that unprivileged users cannot read NT endpoints."""
        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.get()

    def test_notification_template_read_as_org_admin(self, factories, organization, org_admin):
        """Tests that org_admins can read NT endpoints."""
        notification_template = factories.notification_template(organization=organization)

        with self.current_user(username=org_admin.username, password=org_admin.password):
            notification_template.get()

    def test_notification_template_edit_as_unprivileged_user(self, email_notification_template, unprivileged_user):
        """Tests that unprivileged users cannot edit NTs."""
        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.put()
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.patch()

    def test_notification_template_edit_as_org_admin(self, factories, organization, org_admin):
        """Tests that org_admins can edit NTs."""
        notification_template = factories.notification_template(organization=organization)

        with self.current_user(username=org_admin.username, password=org_admin.password):
            notification_template.put()
            notification_template.patch()

    def test_notification_template_delete_as_unprivileged_user(self, email_notification_template, unprivileged_user):
        """Tests that unprivileged_users cannot delete NTs."""
        with self.current_user(username=unprivileged_user.username, password=unprivileged_user.password):
            with pytest.raises(towerkit.exceptions.Forbidden):
                email_notification_template.delete()

    def test_notification_template_delete_as_org_admin(self, factories, organization, org_admin):
        """Tests that org_admins can delete NTs."""
        notification_template = factories.notification_template(organization=organization)

        with self.current_user(username=org_admin.username, password=org_admin.password):
            notification_template.delete()

    def test_user_capabilities_as_superuser(self, email_notification_template, api_notification_templates_pg):
        """Tests NT 'user_capabilities' as superuser."""
        check_user_capabilities(email_notification_template, "superuser")
        check_user_capabilities(api_notification_templates_pg.get(id=email_notification_template.id).results.pop(), "superuser")

    def test_user_capabilities_as_org_admin(self, factories, organization, org_admin, api_notification_templates_pg):
        """Tests NT 'user_capabilities' as an org_admin."""
        notification_template = factories.notification_template(organization=organization)

        with self.current_user(username=org_admin.username, password=org_admin.password):
            check_user_capabilities(notification_template.get(), "org_admin")
            check_user_capabilities(api_notification_templates_pg.get(id=notification_template.id).results.pop(), "org_admin")
