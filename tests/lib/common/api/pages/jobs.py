import base
from common.exceptions import *

class Job_Page(base.Task_Page):
    base_url = '/api/v1/jobs/{id}/'

class Jobs_Page(Job_Page, base.Base_List):
    base_url = '/api/v1/jobs/'
