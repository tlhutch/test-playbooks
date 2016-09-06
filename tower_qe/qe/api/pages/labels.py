import fauxfactory

from qe.api.pages import Organization
from qe.api import resources
import base


class Label(base.Base):

    dependencies = [Organization]

    def silent_delete(self):
        '''
        Label pages do not support DELETE requests. Here, we override the base page object
        silent_delete method to account for this.
        '''
        pass

    def create(self, name='', description='', organization=Organization, **kw):
        name = name or 'Label - {}'.format(fauxfactory.gen_alphanumeric())
        description = description or fauxfactory.gen_utf8()
        self.create_and_update_dependencies(organization)
        org_id = self.dependency_store[Organization].id
        return self.update_identity(Labels(self.testsetup).post(dict(name=name, description=description,
                                                                     organization=org_id)))

base.register_page(resources.v1_label, Label)


class Labels(base.BaseList, Label):

    pass

base.register_page([resources.v1_labels,
                    resources.v1_job_labels,
                    resources.v1_job_template_labels], Labels)

# backwards compatibility
Label_Page = Label
Labels_Page = Labels
