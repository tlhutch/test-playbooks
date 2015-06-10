import base


class Permission_Page(base.Base):
    base_url = '/api/v1/users/{id}/permissions/{id}/'

    name = property(base.json_getter('name'), base.json_setter('name'))
    type = property(base.json_getter('type'), base.json_setter('type'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    permission_type = property(base.json_getter('permission_type'), base.json_setter('permission_type'))

    # associations
    user = property(base.json_getter('user'), base.json_setter('user'))
    team = property(base.json_getter('team'), base.json_setter('team'))
    inventory = property(base.json_getter('inventory'), base.json_setter('inventory'))
    project = property(base.json_getter('project'), base.json_setter('project'))


class Permissions_Page(Permission_Page, base.Base_List):
    base_url = '/api/v1/users/{id}/permissions/'
