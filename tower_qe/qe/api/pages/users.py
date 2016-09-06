import fauxfactory

from qe.exceptions import NoContent_Exception
from qe.api import resources
from qe.config import config
import base


class User(base.Base):

    def create(self, username='', password='', organization=None, **kw):
        self.password = password or config.credentials.default.password

        payload = dict(username=username or fauxfactory.gen_alphanumeric(),
                       password=self.password, is_superuser=kw.get('is_superuser', False),
                       first_name=kw.get('first_name', fauxfactory.gen_alphanumeric()),
                       last_name=kw.get('last_name', fauxfactory.gen_alphanumeric()),
                       email=kw.get('email', fauxfactory.gen_email()))
        self.update_identity(Users(self.testsetup).post(payload))

        if organization:
            try:
                organization.related.users.post(dict(id=self.id))
            except NoContent_Exception:
                pass
        return self

base.register_page(resources.v1_user, User)


class Users(base.BaseList, User):

    pass

base.register_page([resources.v1_users,
                    resources.v1_related_users], Users)


class Me(Users):

    pass

base.register_page(resources.v1_me, Me)

# backwards compatibility
User_Page = User
Users_Page = Users
Me_Page = Me
