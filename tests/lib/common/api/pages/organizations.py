import base
from common.exceptions import *

class Organization_Page(base.Base):
    # FIXME - it would be nice for base_url to always return self.json.url.
    base_url = '/api/v1/organizations/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name):
        assert name in self.json['related']
        if name in ['users', 'admins']:
            from users import Users_Page
            related = Users_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'projects':
            from projects import Projects_Page
            related = Projects_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'activity_stream':
            from activity_stream import Activity_Stream_Page
            related = Activity_Stream_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Organizations_Page(Organization_Page, base.Base_List):
    base_url = '/api/v1/organizations/'
