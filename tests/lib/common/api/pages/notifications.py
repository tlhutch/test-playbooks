from common.api.pages import Base, Base_List, json_getter, json_setter


class Notification_Page(Base):
    base_url = '/api/v1/notifications/{id}/'
    id = property(json_getter('id'), json_setter('id'))
    type = property(json_getter('type'), json_setter('type'))
    url = property(json_getter('url'), json_setter('url'))
    created = property(json_getter('created'), json_setter('created'))
    modified = property(json_getter('modified'), json_setter('modified'))
    notification_template = property(json_getter('notification_template'), json_setter('notification_template'))
    error = property(json_getter('error'), json_setter('error'))
    status = property(json_getter('status'), json_setter('status'))
    notifications_sent = property(json_getter('notifications_sent'), json_setter('notifications_sent'))
    notification_type = property(json_getter('notification_type'), json_setter('notification_type'))
    recipients = property(json_getter('recipients'), json_setter('recipients'))
    subject = property(json_getter('subject'), json_setter('subject'))

    def __str__(self):
        return "<%s id:%s, notification_type:%s, status:%s, error:%s, " \
            "notifications_sent:%s, subject:%s, recipients:%s>" % \
            (self.__class__.__name__, self.id, self.notification_type, self.status,
             self.error, self.notifications_sent, self.subject, self.recipients)

    @property
    def is_successful(self):
        '''
        Return whether the notification was created successfully. This means that:
         * self.status == 'successful'
         * self.error == False
        '''
        return 'successful' == self.status.lower() and not self.error


class Notifications_Page(Notification_Page, Base_List):
    base_url = '/api/v1/notifications/'
