import time

from common.api import resources
import common.utils
import base


class Notification(base.Base):

    def __str__(self):
        output = "<%s id:%s, notification_type:%s, status:%s, error:%s, " \
                 "notifications_sent:%s, subject:%s, recipients:%s>" % \
                 (self.__class__.__name__, self.id, self.notification_type, self.status,
                  self.error, self.notifications_sent, self.subject, self.recipients)
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

    def wait_until_status(self, status, interval=1, verbose=0, timeout=30):
        if not isinstance(status, (list, tuple)):
            '''coerce 'status' parameter to a list'''
            status = [status]
        return common.utils.wait_until(
            self, 'status', status,
            interval=interval, verbose=verbose, timeout=timeout,
            start_time=time.strptime(self.created, '%Y-%m-%dT%H:%M:%S.%fZ'))

    def wait_until_completed(self, interval=1, verbose=0, timeout=30):
        return self.wait_until_status(
            ('successful', 'failed',),
            interval=interval, verbose=verbose, timeout=timeout)

base.register_page(resources.v1_notification, Notification)


class Notifications(Notification, base.BaseList):

    def wait_until_count(self, count, interval=1, verbose=0, timeout=60):
        '''
        Poll notifications page until it is populated with `count` number of notifications.
        '''
        return common.utils.wait_until(
            self, 'count', count,
            interval=interval, verbose=verbose, timeout=timeout)

base.register_page([resources.v1_notifications,
                    resources.v1_job_notifications,
                    resources.v1_notification_template_notifications,
                    resources.v1_system_job_notifications], Notifications)

# backwards compatibility
Notification_Page = Notification
Notifications_Page = Notifications
