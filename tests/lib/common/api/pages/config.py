import base
from common.exceptions import *

class Config_Page(base.Base):
    base_url = '/api/v1/config/'
    version = property(base.json_getter('version'), base.json_setter('version'))
    license_info = property(base.json_getter('license_info'), base.json_setter('license_info'))
    ansible_version = property(base.json_getter('ansible_version'), base.json_setter('ansible_version'))
    time_zone = property(base.json_getter('time_zone'), base.json_setter('time_zone'))
