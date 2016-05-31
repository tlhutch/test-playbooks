import fauxfactory
import base
from users import Users_Page


class Team_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/teams/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    type = property(base.json_getter('type'), base.json_setter('type'))
    description = property(base.json_getter('description'), base.json_setter('description'))
    organization = property(base.json_getter('organization'), base.json_setter('organization'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'users':
            cls = Users_Page
        elif attr == 'organization':
            from organizations import Organization_Page
            cls = Organization_Page
        elif attr == 'credentials':
            from credentials import Credentials_Page
            cls = Credentials_Page
        elif attr in ['object_roles', 'roles']:
            from roles import Roles_Page
            cls = Roles_Page
        elif attr in ['created_by', 'modified_by']:
            from users import User_Page
            cls = User_Page
        elif attr == 'projects':
            from projects import Projects_Page
            cls = Projects_Page
        elif attr == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            cls = Activity_Stream_Page
        elif attr == 'access_list':
            from access_list import Access_List_Page
            cls = Access_List_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)

    def add_permission(self, permission_type, project=None, inventory=None, run_ad_hoc_commands=None):
        perm_pg = self.get_related('permissions')
        payload = dict(name=fauxfactory.gen_utf8(),
                       description=fauxfactory.gen_utf8(),
                       user=self.id,
                       permission_type=permission_type,
                       project=project,
                       inventory=inventory,
                       run_ad_hoc_commands=run_ad_hoc_commands)
        result = perm_pg.post(payload)
        return result


class Teams_Page(Team_Page, base.Base_List):
    base_url = '/api/v1/teams/'
