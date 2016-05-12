from common.api.pages import Base, Base_List, json_getter, json_setter


class Notification_Template_Page(Base):
    base_url = '/api/v1/notification_templates/{id}/'
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

    def test(self):
        '''Create test notification'''
        assert 'test' in self.json['related'], \
            "No such related attribute 'test'"

        test_pg = Notification_Template_Test_Page(self.testsetup, base_url=self.json['related']['test'])
        return test_pg.post()


class Notification_Templates_Page(Notification_Template_Page, Base_List):
    base_url = '/api/v1/notification_templates/'


class Notification_Template_Test_Page(Base):
    base_url = '/api/v1/notification_templates/{id}/test/'
    notification = property(json_getter('notification'), json_setter('notification'))
