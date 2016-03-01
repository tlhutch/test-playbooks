from common.api.pages import Base, Base_List, json_getter, json_setter


class Notification_Page(Base):
    base_url = '/api/v1/notifications/{id}/'
    id = property(json_getter('id'), json_setter('id'))
    type = property(json_getter('type'), json_setter('type'))
    url = property(json_getter('url'), json_setter('url'))
    created = property(json_getter('created'), json_setter('created'))
    modified = property(json_getter('modified'), json_setter('modified'))
    notifier = property(json_getter('notifier'), json_setter('notifier'))
    error = property(json_getter('error'), json_setter('error'))
    status = property(json_getter('status'), json_setter('status'))
    notifications_sent = property(json_getter('notifications_sent'), json_setter('notifications_sent'))
    notification_type = property(json_getter('notification_type'), json_setter('notification_type'))
    recipients = property(json_getter('recipients'), json_setter('recipients'))
    subject = property(json_getter('subject'), json_setter('subject'))


class Notifications_Page(Notification_Page, Base_List):
    base_url = '/api/v1/notifications/'
