from common.api.pages import Base, Base_List, json_setter, json_getter


class Label_Page(Base):
    base_url = '/api/v1/labels/{id}/'
    type = property(json_getter('type'), json_setter('type'))
    created = property(json_getter('created'), json_setter('created'))
    modified = property(json_getter('modified'), json_setter('modified'))
    name = property(json_getter('name'), json_setter('name'))
    organization = property(json_getter('organization'), json_setter('organization'))

    def get_related(self, attr, **kwargs):
        assert attr in self.json['related'], \
            "No such related attribute '%s'" % attr

        if attr == 'created_by':
            from users import User_Page
            cls = User_Page
        elif attr == 'modified_by':
            from users import User_Page
            cls = User_Page
        elif attr == 'organization':
            from organizations import Organization_Page
            cls = Organization_Page
        else:
            raise NotImplementedError("No related class found for '%s'" % attr)

        return cls(self.testsetup, base_url=self.json['related'][attr]).get(**kwargs)

    def silent_delete(self):
        '''
        Label pages do not support DELETE requests. Here, we override the base page object
        silent_delete method to account for this.
        '''
        pass


class Labels_Page(Label_Page, Base_List):
    base_url = '/api/v1/labels/'
