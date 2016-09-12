import fauxfactory

from qe.api import resources
import qe.exceptions
import base


class Organization(base.Base):

    def add_admin(self, user):
        if isinstance(user, base.Base):
            user = user.json
        try:
            self.related.admins.post(user)
        except qe.exceptions.NoContent_Exception:
            pass

    def add_user(self, user):
        if isinstance(user, base.Base):
            user = user.json
        try:
            self.related.users.post(user)
        except qe.exceptions.NoContent_Exception:
            pass

    def create(self, name='', description='', **kw):
        name = name or 'Organization - {}'.format(fauxfactory.gen_alphanumeric())
        description = description or fauxfactory.gen_alphanumeric()
        return self.update_identity(Organizations(self.testsetup).post(dict(name=name, description=description)))

base.register_page(resources.v1_organization, Organization)


class Organizations(base.BaseList, Organization):

    pass

base.register_page([resources.v1_organizations,
                    resources.v1_user_organizations,
                    resources.v1_project_organizations], Organizations)

# backwards compatibility
Organization_Page = Organization
Organizations_Page = Organizations
