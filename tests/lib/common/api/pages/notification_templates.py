from common.api.pages import Base, Base_List, json_getter, json_setter
import common.exceptions


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
    summary_fields = property(json_getter('summary_fields'), json_setter('summary_fields'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'notifications':
            from notifications import Notifications_Page
            cls = Notifications_Page
        elif attr == 'organization':
            from organizations import Organization_Page
            cls = Organization_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)

    def test(self):
        '''Create test notification'''
        assert 'test' in self.json['related'], \
            "No such related attribute 'test'"
        # get related->test
        test_pg = Notification_Template_Test_Page(self.testsetup, base_url=self.json['related']['test'])

        # trigger test notification
        notification_id = test_pg.post().notification

        # return notification page
        notifications_pg = self.get_related('notifications', id=notification_id).wait_until_count(1)
        assert notifications_pg.count == 1, \
            "test notification triggered (id:%s) but notification not found in response at %s/notifications/" % \
            (notification_id, self.url)
        return notifications_pg.results[0]

    def silent_delete(self):
        '''
        Delete the Notification Template, ignoring the exception that is raised
        if there are notifications pending.
        '''
        try:
            super(Notification_Template_Page, self).silent_delete()
        except (common.exceptions.Method_Not_Allowed_Exception):
            pass


class Notification_Templates_Page(Notification_Template_Page, Base_List):
    base_url = '/api/v1/notification_templates/'


class Notification_Template_Test_Page(Base):
    base_url = '/api/v1/notification_templates/{id}/test/'
    notification = property(json_getter('notification'), json_setter('notification'))
