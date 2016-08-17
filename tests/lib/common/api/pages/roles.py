from common.api import resources
import base


class Role_Page(base.Base):

    pass

base.register_page(resources.v1_role, Role_Page)


class Roles_Page(Role_Page, base.Base_List):

    pass

base.register_page([resources.v1_roles,
                    resources.v1_related_roles,
                    resources.v1_related_object_roles], Roles_Page)
