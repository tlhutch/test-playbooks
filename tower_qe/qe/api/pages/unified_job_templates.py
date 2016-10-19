from qe.api import resources
from qe.utils import to_str, wait_until
import base


class UnifiedJobTemplate(base.Base):
    '''
    Base class for unified job template pages (e.g. project, inventory_source,
    and job_template).
    '''
    def __str__(self):
        # NOTE: I use .replace('%', '%%') to workaround an odd string
        # formatting issue where result_stdout contained '%s'.  This later caused
        # a python traceback when attempting to display output from this method.
        items = ['id', 'name', 'status', 'source', 'last_update_failed', 'last_updated',
                 'result_traceback', 'job_explanation', 'job_args']
        info = []
        for item in filter(lambda x: hasattr(self, x), items):
            info.append('{0}:{1}'.format(item, to_str(getattr(self, item))))
        output = '<{0.__class__.__name__} {1}>'.format(self, ', '.join(info))
        return output.replace('%', '%%')

    def wait_until_started(self, interval=1, verbose=0, timeout=60):
        '''Wait until a unified_job_template has started.'''
        return wait_until(self, 'status', ('new', 'pending', 'waiting', 'running',),
                          interval=interval, verbose=verbose, timeout=timeout)

    def wait_until_completed(self, interval=5, verbose=0, timeout=60 * 8):
        '''Wait until a unified_job_template has completed.'''
        return wait_until(self, 'status', ('successful', 'failed', 'error', 'canceled',),
                          interval=interval, verbose=verbose, timeout=timeout)

    @property
    def is_successful(self):
        '''An unified_job_template is considered successful when:
            1) status == 'successful'
            2) not last_update_failed
            3) last_updated
        '''
        return self.status == 'successful' and \
            not self.last_update_failed and \
            self.last_updated is not None

base.register_page(resources.v1_unified_job_template, UnifiedJobTemplate)


class UnifiedJobTemplates(base.BaseList, UnifiedJobTemplate):

    pass

base.register_page(resources.v1_unified_job_templates, UnifiedJobTemplates)

# backwards compatibility
Unified_Job_Template_Page = UnifiedJobTemplate
Unified_Job_Templates_Page = UnifiedJobTemplates
