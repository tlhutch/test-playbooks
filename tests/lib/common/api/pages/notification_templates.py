from common.api import resources
import common.exceptions
import base


class Notification_Template_Page(base.Base):

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

base.register_page([resources.v1_notification_template,
                    resources.v1_notification_template_any,
                    resources.v1_notification_template_error,
                    resources.v1_notification_template_success], Notification_Template_Page)


class Notification_Templates_Page(Notification_Template_Page, base.Base_List):

    pass

base.register_page([resources.v1_notification_templates,
                    resources.v1_notification_templates_any,
                    resources.v1_notification_templates_error,
                    resources.v1_notification_templates_success], Notification_Templates_Page)


class Notification_Template_Test_Page(base.Base):

    pass

base.register_page(resources.v1_notification_template_test, Notification_Template_Test_Page)
