import time

from qe.api import resources
import qe.utils
import base


class Notification(base.Base):

    def __str__(self):
        items = ['id', 'notification_type', 'status', 'error', 'notifications_sent',
                 'subject', 'recipients']
        info = ', '.join(['{0}:{1}'.format(item, getattr(self, item)) for item in items if hasattr(self, item)])
        output = '<{0.__class__.__name__} {1}>'.format(self, info)
        return output.replace('%', '%%').encode("ascii", "backslashreplace")

    def __repr__(self):
        return self.__str__()

    @property
    def is_completed(self):
        '''
        Return whether the current task has finished.  This does not indicate
        whether the task completed successfully.
        '''
        return self.status in ['successful', 'failed']

    @property
    def is_successful(self):
        '''
        Return whether the notification was created successfully. This means that:
         * self.status == 'successful'
         * self.error == False
        '''
        return 'successful' == self.status and not self.error

    def wait_until_status(self, status, interval=5, verbose=0, timeout=30):
        if not isinstance(status, (list, tuple)):
            '''coerce 'status' parameter to a list'''
            status = [status]
        return qe.utils.wait_until(
            self, 'status', status,
            interval=interval, verbose=verbose, timeout=timeout,
            start_time=time.strptime(self.created, '%Y-%m-%dT%H:%M:%S.%fZ'))

    def wait_until_completed(self, interval=5, verbose=0, timeout=30):
        return self.wait_until_status(
            ('successful', 'failed',),
            interval=interval, verbose=verbose, timeout=timeout)

base.register_page(resources.v1_notification, Notification)


class Notifications(base.BaseList, Notification):

    def wait_until_count(self, count, interval=10, verbose=0, timeout=3*60):
        '''
        Poll notifications page until it is populated with `count` number of notifications.
        '''
        return qe.utils.wait_until(
            self, 'count', count,
            interval=interval, verbose=verbose, timeout=timeout)

base.register_page([resources.v1_notifications,
                    resources.v1_job_notifications,
                    resources.v1_notification_template_notifications,
                    resources.v1_system_job_notifications], Notifications)

# backwards compatibility
Notification_Page = Notification
Notifications_Page = Notifications
