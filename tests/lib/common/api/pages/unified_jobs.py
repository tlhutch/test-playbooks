import time
import common.utils
from common.api.pages import Base, json_getter, json_setter


class Unified_Job_Page(Base):
    '''
    Base class for unified job pages (e.g. project_updates, inventory_updates
    and jobs).
    '''

    id = property(json_getter('id'), json_setter('id'))
    name = property(json_getter('name'), json_setter('name'))
    type = property(json_getter('type'), json_setter('type'))
    status = property(json_getter('status'), json_setter('status'))
    failed = property(json_getter('failed'), json_setter('failed'))
    result_traceback = property(json_getter('result_traceback'), json_setter('result_traceback'))
    result_stdout = property(json_getter('result_stdout'), json_setter('result_stdout'))
    job_explanation = property(json_getter('job_explanation'), json_setter('job_explanation'))
    created = property(json_getter('created'), json_setter('created'))
    modified = property(json_getter('modified'), json_setter('modified'))
    started = property(json_getter('started'), json_setter('started'))
    finished = property(json_getter('finished'), json_setter('finished'))
    launch_type = property(json_getter('launch_type'), json_setter('launch_type'))
    job_type = property(json_getter('job_type'), json_setter('job_type'))
    job_env = property(json_getter('job_env'), json_setter('job_env'))
    job_args = property(json_getter('job_args'), json_setter('job_args'))
    limit = property(json_getter('limit'), json_setter('limit'))
    summary_fields = property(json_getter('summary_fields'), json_setter('summary_fields'))

    def __str__(self):
        # NOTE: I use .replace('%', '%%') to workaround an odd string
        # formatting issue where result_stdout contained '%s'.  This later caused
        # a python traceback when attempting to display output from this method.
        output = "<%s id:%s, name:%s, status:%s, failed:%s, result_stdout:%s, " \
            "result_traceback:%s, job_explanation:%s, job_args:%s>" % \
            (self.__class__.__name__, self.id, self.name, self.status, self.failed,
             self.result_stdout, self.result_traceback,
             self.job_explanation, self.job_args)
        return output.replace('%', '%%')

    @property
    def is_completed(self):
        '''
        Return whether the current task has finished.  This does not indicate
        whether the task completed successfully.
        '''
        return self.status.lower() in ['successful', 'failed', 'error', 'canceled']

    @property
    def is_successful(self):
        '''
        Return whether the current has completed successfully.  This means that:
         * self.status == 'successful'
         * self.has_traceback == False
         * self.failed == False
        '''
        return 'successful' == self.status.lower() and \
            not (self.has_traceback or self.failed)

    @property
    def has_traceback(self):
        '''
        Return whether a traceback has been detected in result_traceback or
        result_stdout
        '''
        return 'Traceback' in self.result_traceback or \
               'Traceback' in self.result_stdout

    def wait_until_status(self, status, interval=1, verbose=0, timeout=60):
        if not isinstance(status, (list, tuple)):
            '''coerce 'status' parameter to a list'''
            status = [status]
        return common.utils.wait_until(
            self, 'status', status,
            interval=interval, verbose=verbose, timeout=timeout,
            start_time=time.strptime(self.created, '%Y-%m-%dT%H:%M:%S.%fZ'))

    def wait_until_started(self, interval=1, verbose=0, timeout=60):
        return self.wait_until_status(
            ('pending', 'running', 'successful', 'failed', 'error', 'canceled',),
            interval=interval, verbose=verbose, timeout=timeout)

    def wait_until_completed(self, interval=5, verbose=0, timeout=60 * 2):
        return self.wait_until_status(
            ('successful', 'failed', 'error', 'canceled',),
            interval=interval, verbose=verbose, timeout=timeout)
