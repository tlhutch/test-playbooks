from common.api import resources
import common.exceptions
import base


class Organization_Page(base.Base):

    def add_admin(self, user):
        if isinstance(user, base.Base):
            user = user.json
        try:
            self.get_related('admins').post(user)
        except common.exceptions.NoContent_Exception:
            pass

    def add_user(self, user):
        if isinstance(user, base.Base):
            user = user.json
        try:
            self.get_related('users').post(user)
        except common.exceptions.NoContent_Exception:
            pass

base.register_page(resources.v1_organization, Organization_Page)


class Organizations_Page(Organization_Page, base.Base_List):

    pass

base.register_page([resources.v1_organizations,
                    resources.v1_user_organizations,
                    resources.v1_project_organizations], Organizations_Page)
