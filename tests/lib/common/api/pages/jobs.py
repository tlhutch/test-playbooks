import base
from common.exceptions import *

class Job_Page(base.Base):
    base_url = '/api/v1/jobs/{id}/'
    status = property(base.json_getter('status'), base.json_setter('status'))
    failed = property(base.json_getter('failed'), base.json_setter('failed'))
    result_traceback = property(base.json_getter('result_traceback'), base.json_setter('result_traceback'))
    result_stdout = property(base.json_getter('result_stdout'), base.json_setter('result_stdout'))

class Jobs_Page(Job_Page, base.Base_List):
    base_url = '/api/v1/jobs/'
