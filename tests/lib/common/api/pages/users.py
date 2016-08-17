from common.api import resources
import base


class User_Page(base.Base):

    pass

base.register_page(resources.v1_user, User_Page)


class Users_Page(User_Page, base.Base_List):

    pass

base.register_page([resources.v1_users,
                    resources.v1_related_users], Users_Page)


class Me_Page(Users_Page):

    pass

base.register_page(resources.v1_me, Me_Page)
