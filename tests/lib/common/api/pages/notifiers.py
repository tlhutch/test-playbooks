from common.api.pages import Base, Base_List, json_getter, json_setter


class Notifier_Page(Base):
    base_url = '/api/v1/notifiers/{id}/'
    id = property(json_getter('id'), json_setter('id'))
    type = property(json_getter('type'), json_setter('type'))
    url = property(json_getter('url'), json_setter('url'))
    created = property(json_getter('created'), json_setter('created'))
    modified = property(json_getter('modified'), json_setter('modified'))
    name = property(json_getter('name'), json_setter('name'))
    description = property(json_getter('description'), json_setter('description'))
    organization = property(json_getter('organization'), json_setter('organization'))
    notification_type = property(json_getter('notification_type'), json_setter('notification_type'))
    notification_configuration = property(json_getter('notification_configuration'), json_setter('notification_configuration'))


class Notifiers_Page(Notifier_Page, Base_List):
    base_url = '/api/v1/notifiers/'
