from qe.api import resources
import base


class Role(base.Base):

    pass

base.register_page(resources.v1_role, Role)


class Roles(Role, base.BaseList):

    pass

base.register_page([resources.v1_roles,
                    resources.v1_related_roles,
                    resources.v1_related_object_roles], Roles)

# backwards compatibility
Role_Page = Role
Roles_Page = Roles
