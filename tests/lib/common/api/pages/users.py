from common.api import resources
import base


class User(base.Base):

    pass

base.register_page(resources.v1_user, User)


class Users(User, base.BaseList):

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
