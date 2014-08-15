import base
from common.exceptions import *

class Dashboard_Page(base.Base):
    base_url = '/api/v1/dashboard/'
    inventory_sources = property(base.json_getter('inventory_sources'), base.json_setter('inventory_sources'))
    hosts = property(base.json_getter('hosts'), base.json_setter('hosts'))
    groups = property(base.json_getter('groups'), base.json_setter('groups'))
    projects = property(base.json_getter('projects'), base.json_setter('projects'))
    organizations = property(base.json_getter('organizations'), base.json_setter('organizations'))
    teams = property(base.json_getter('teams'), base.json_setter('teams'))
    users = property(base.json_getter('users'), base.json_setter('users'))
    credentials = property(base.json_getter('credentials'), base.json_setter('credentials'))
    jobs = property(base.json_getter('jobs'), base.json_setter('jobs'))
    job_templates = property(base.json_getter('job_templates'), base.json_setter('job_templates'))
