from qe.api import resources
import base


class Label(base.Base):

    def silent_delete(self):
        '''
        Label pages do not support DELETE requests. Here, we override the base page object
        silent_delete method to account for this.
        '''
        pass

base.register_page(resources.v1_label, Label)


class Labels(Label, base.BaseList):

    pass

base.register_page([resources.v1_labels,
                    resources.v1_job_labels,
                    resources.v1_job_template_labels], Labels)

# backwards compatibility
Label_Page = Label
Labels_Page = Labels
