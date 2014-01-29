import time
import base
import common.utils
from common.exceptions import *

class Job_Page(base.Base):
    base_url = '/api/v1/jobs/{id}/'
    status = property(base.json_getter('status'), base.json_setter('status'))
    failed = property(base.json_getter('failed'), base.json_setter('failed'))
    result_traceback = property(base.json_getter('result_traceback'), base.json_setter('result_traceback'))
    result_stdout = property(base.json_getter('result_stdout'), base.json_setter('result_stdout'))
    created = property(base.json_getter('created'), base.json_setter('created'))
    modified = property(base.json_getter('modified'), base.json_setter('failed'))

    @property
    def is_successful(self):
        return 'successful' == self.status.lower()

    def wait_until_completed(self, interval=5, verbose=0, timeout=60*8):
        return common.utils.wait_until(self, 'status', ('successful', 'failed', 'error', 'canceled',),
            interval=interval, verbose=verbose, timeout=timeout,
            start_time=time.strptime(self.created, '%Y-%m-%dT%H:%M:%S.%fZ'))

class Jobs_Page(Job_Page, base.Base_List):
    base_url = '/api/v1/jobs/'
