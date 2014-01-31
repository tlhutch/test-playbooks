import base
from common.exceptions import *

class Project_Page(base.Base):
    base_url = '/api/v1/projects/{id}/'
    name = property(base.json_getter('name'), base.json_setter('name'))
    description = property(base.json_getter('description'), base.json_setter('description'))

    def get_related(self, name):
        assert name in self.json['related']
        if name == 'last_update':
            related = Project_Update_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'project_updates':
            related = Project_Updates_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'update':
            related = base.Base(self.testsetup, base_url=self.json['related'][name])
        elif name == 'organizations':
            from organizations import Organizations_Page
            related = Organizations_Page(self.testsetup, base_url=self.json['related'][name])
        elif name == 'teams':
            from teams import Teams_Page
            related = Teams_Page(self.testsetup, base_url=self.json['related'][name])
        else:
            raise NotImplementedError
        return related.get()

class Projects_Page(Project_Page, base.Base_List):
    base_url = '/api/v1/projects/'

class Project_Update_Page(base.Task_Page):
    base_url = '/api/v1/project/{id}/update/'

class Project_Updates_Page(Project_Update_Page, base.Base_List):
    base_url = '/api/v1/projects/{id}/project_updates/'
