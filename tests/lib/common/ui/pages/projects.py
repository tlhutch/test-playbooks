from selenium.webdriver.common.by import By
from common.ui.pages import MainTab_Page
from common.ui.pages.forms import Form_Page, input_getter_by_name, input_setter_by_name
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button, Select_Button  # NOQA
from common.ui.pages.regions.dialogs import Prompt_Dialog  # NOQA
from common.ui.pages.regions.lists import List_Region  # NOQA


class Projects_Page(MainTab_Page):
    '''Describes projects page'''
    _tab_title = "Projects"
    _related = {
        'add': 'Project_Create_Page',
        'edit': 'Project_Edit_Page',
        'delete': 'Prompt_Dialog',
        'activity_stream': 'Projects_Activity_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#projects_table'),
        'pagination': (By.CSS_SELECTOR, '#project-pagination'),
    }


class Projects_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all projects'''
    _tab_title = "Projects"
    _related = {
        'close': 'Projects_Page',
    }


class Project_Create_Page(Form_Page):
    '''Describes the projects create page'''
    _tab_title = "Projects"
    _breadcrumb_title = 'Create Project'
    _related = {
        'save': 'Projects_Page',
    }
    _locators = {
        'form': (By.CSS_SELECTOR, '#project_form'),
        'name': (By.CSS_SELECTOR, '#project_name'),
        'description': (By.CSS_SELECTOR, '#project_description'),
        'organization_btn': (By.CSS_SELECTOR, '#organization-lookup-btn'),
        'organization_name': (By.CSS_SELECTOR, "input[name='organization_name']"),
        'scm_type': (By.CSS_SELECTOR, '#project_scm_type'),
        'base_dir': (By.CSS_SELECTOR, '#project_base_dir'),
        # scm_type == 'git'
        'scm_url': (By.CSS_SELECTOR, '#project_scm_url'),
        'scm_branch': (By.CSS_SELECTOR, '#project_scm_branch'),
        'credential_btn': (By.CSS_SELECTOR, '#credential-lookup-btn'),
        'credential_name': (By.CSS_SELECTOR, "input[name='credential_name']"),
        'scm_clean': (By.CSS_SELECTOR, '#project_scm_clean_chbox'),
        'scm_delete_on_update': (By.CSS_SELECTOR, '#project_scm_delete_on_update_chbox'),
        'scm_update_on_launch': (By.CSS_SELECTOR, '#project_scm_update_on_launch_chbox'),
        # Help buttons
        'clean_help': (By.CSS_SELECTOR, '#awp-scm_clean'),
        'delete_on_update_help': (By.CSS_SELECTOR, '#awp-scm_delete_on_update'),
        'update_on_launch_help': (By.CSS_SELECTOR, '#awp-scm_update_on_launch'),
        # Form Buttons
        'save_btn': (By.CSS_SELECTOR, '#project_save_btn'),
        'reset_btn': (By.CSS_SELECTOR, '#project_reset_btn'),
    }

    name = property(input_getter_by_name('name'), input_setter_by_name('name'))
    description = property(input_getter_by_name('description'), input_setter_by_name('description'))
    organization_name = property(input_getter_by_name('organization_name'), input_setter_by_name('organization_name'))
    scm_type = property(input_getter_by_name('scm_type'), input_setter_by_name('scm_type'))

    # scm_type == 'git'
    credential_name = property(input_getter_by_name('credential_name'), input_setter_by_name('credential_name'))
    scm_url = property(input_getter_by_name('scm_url'), input_setter_by_name('scm_url'))
    scm_branch = property(input_getter_by_name('scm_branch'), input_setter_by_name('scm_branch'))
    scm_clean = property(input_getter_by_name('scm_clean'), input_setter_by_name('scm_clean'))
    scm_delete_on_update = property(input_getter_by_name('scm_delete_on_update'), input_setter_by_name('scm_delete_on_update'))
    scm_update_on_launch = property(input_getter_by_name('scm_update_on_launch'), input_setter_by_name('scm_update_on_launch'))

    @property
    def clean_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['clean_help']))

    @property
    def delete_on_update_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['delete_on_update_help']))

    @property
    def update_on_launch_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['update_on_launch_help']))


class Project_Edit_Page(Project_Create_Page):
    _tab_title = "Projects"
    _related = Project_Create_Page._related
    _related.update({
        'activity_stream': 'Project_Activity_Page',
        'scm_update': 'Projects_Page',
    })
    _locators = Project_Create_Page._locators
    _locators.update({
        'scm_update_btn': (By.CSS_SELECTOR, '#scm_update_btn'),
    })

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match object name'''
        return self.name

    @property
    def scm_update_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('scm_update'))

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))


class Project_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Projects"
    _related = {
        'close': 'Project_Edit_Page',
    }
