import base

import common.exceptions


class Organization_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/organizations/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    type = property(base.json_getter('type'), base.json_setter('type'))
    summary_fields = property(base.json_getter('summary_fields'), base.json_setter('summary_fields'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr in ['users', 'admins']:
            from users import Users_Page
            cls = Users_Page
        elif attr in ['created_by', 'modified_by']:
            from users import User_Page
            cls = User_Page
        elif attr == 'teams':
            from teams import Teams_Page
            cls = Teams_Page
        elif attr == 'inventories':
            from inventory import Inventories_Page
            cls = Inventories_Page
        elif attr == 'projects':
            from projects import Projects_Page
            cls = Projects_Page
        elif attr == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            cls = Activity_Stream_Page
        elif attr in ['notification_templates', 'notification_templates_any', 'notification_templates_error', 'notification_templates_success']:
            from notification_templates import Notification_Templates_Page
            cls = Notification_Templates_Page
        elif attr == 'access_list':
            from access_list import Access_List_Page
            cls = Access_List_Page
        elif attr == 'credentials':
            from credentials import Credentials_Page
            cls = Credentials_Page
        elif attr == 'inventories':
            from inventory import Inventories_Page
            cls = Inventories_Page
        elif attr == 'projects':
            from projects import Projects_Page
            cls = Projects_Page
        elif attr == 'object_roles':
            from roles import Roles_Page
            cls = Roles_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)

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


class Organizations_Page(Organization_Page, base.Base_List):
    base_url = '/api/v1/organizations/'
