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
        'owner': (By.CSS_SELECTOR, "input[name='owner']"),
        'user_btn': (By.CSS_SELECTOR, '#user-lookup-btn'),
        'user_username': (By.CSS_SELECTOR, "input[name='user_username']"),
        'team_btn': (By.CSS_SELECTOR, '#team-lookup-btn'),
        'team_name': (By.CSS_SELECTOR, "input[name='team_name']"),
        'project_kind': (By.CSS_SELECTOR, '#project_kind'),
        'login_method': (By.CSS_SELECTOR, "input[name='login_method']"),
        # ssh_username
        'project_username': (By.CSS_SELECTOR, '#project_username'),
        # ssh_password
        'project_ssh_password_ask': (By.CSS_SELECTOR, '#project_ssh_password_ask_chbox'),
        'project_ssh_password': (By.CSS_SELECTOR, '#project_ssh_password'),
        'project_ssh_password_confirm': (By.CSS_SELECTOR, '#project_ssh_password_confirm'),
        'project_ssh_password_clear_btn': (By.CSS_SELECTOR, '#project_ssh_password_clear_btn'),
        # key_data
        'project_ssh_key_data': (By.CSS_SELECTOR, '#project_ssh_key_data'),
        # key_data_unlock
        'project_ssh_key_unlock_ask': (By.CSS_SELECTOR, '#project_ssh_key_unlock_ask_chbox'),
        'project_ssh_key_unlock': (By.CSS_SELECTOR, '#project_ssh_key_unlock'),
        'project_ssh_key_unlock_confirm': (By.CSS_SELECTOR, '#project_ssh_key_unlock_confirm'),
        'project_ssh_key_unlock_clear_btn': (By.CSS_SELECTOR, '#project_ssh_key_unlock_clear_btn'),
        # vault_password
        'project_vault_password_ask': (By.CSS_SELECTOR, '#project_vault_password_ask_chbox'),
        'project_vault_password': (By.CSS_SELECTOR, '#project_vault_password'),
        'project_vault_password_confirm': (By.CSS_SELECTOR, '#project_vault_password_confirm'),
        'project_vault_password_clear_btn': (By.CSS_SELECTOR, '#project_vault_password_clear_btn'),
        # vCenter
        'project_host': (By.CSS_SELECTOR, '#project_host'),
        'project_password': (By.CSS_SELECTOR, '#project_password'),
        'project_password_confirm': (By.CSS_SELECTOR, '#project_password_confirm'),
        # Azure
        'project_subscription_id': (By.CSS_SELECTOR, '#project_subscription_id'),
        # GCE
        'project_email_address': (By.CSS_SELECTOR, '#project_email_address'),
        # Help buttons
        'owner_help': (By.CSS_SELECTOR, '#awp-owner'),
        'kind_help': (By.CSS_SELECTOR, '#awp-kind'),
        'project_ssh_key_data_help': (By.CSS_SELECTOR, '#awp-ssh_key_data'),
        'login_method_help': (By.CSS_SELECTOR, '#awp-login_method'),
        'project_subscription_id_help': (By.CSS_SELECTOR, '#awp-subscription_id'),
        'project_email_address_help': (By.CSS_SELECTOR, '#awp-email_address'),
        # Form Buttons
        'save_btn': (By.CSS_SELECTOR, '#project_save_btn'),
        'reset_btn': (By.CSS_SELECTOR, '#project_reset_btn'),
    }

    name = property(input_getter_by_name('name'), input_setter_by_name('name'))
    description = property(input_getter_by_name('description'), input_setter_by_name('description'))
    owner = property(input_getter_by_name('owner'), input_setter_by_name('owner'))
    user_username = property(input_getter_by_name('user_username'), input_setter_by_name('user_username'))
    team_name = property(input_getter_by_name('team_name'), input_setter_by_name('team_name'))
    project_kind = property(input_getter_by_name('project_kind'), input_setter_by_name('project_kind'))
    login_method = property(input_getter_by_name('login_method'), input_setter_by_name('login_method'))
    # username
    project_username = property(input_getter_by_name('project_username'), input_setter_by_name('project_username'))
    # ssh_password
    project_ssh_password_ask = property(input_getter_by_name('project_ssh_password_ask'), input_setter_by_name('project_ssh_password_ask'))
    project_ssh_password = property(input_getter_by_name('project_ssh_password'), input_setter_by_name('project_ssh_password'))
    project_ssh_password_confirm = property(input_getter_by_name('project_ssh_password_confirm'), input_setter_by_name('project_ssh_password_confirm'))
    # key_data
    project_ssh_key_data = property(input_getter_by_name('project_ssh_key_data'), input_setter_by_name('project_ssh_key_data'))
    # key_unlock
    project_ssh_key_unlock_ask = property(input_getter_by_name('project_ssh_key_unlock_ask'), input_setter_by_name('project_ssh_key_unlock_ask'))
    project_ssh_key_unlock = property(input_getter_by_name('project_ssh_key_unlock'), input_setter_by_name('project_ssh_key_unlock'))
    project_ssh_key_unlock_confirm = property(input_getter_by_name('project_ssh_key_unlock_confirm'), input_setter_by_name('project_ssh_key_unlock_confirm'))
    # vault
    project_vault_password_ask = property(input_getter_by_name('project_vault_password_ask'), input_setter_by_name('project_vault_password_ask'))
    project_vault_password = property(input_getter_by_name('project_vault_password'), input_setter_by_name('project_vault_password'))
    project_vault_password_confirm = property(input_getter_by_name('project_vault_password_confirm'), input_setter_by_name('project_vault_password_confirm'))
    # vCenter
    project_host = property(input_getter_by_name('project_host'), input_setter_by_name('project_host'))
    project_password = property(input_getter_by_name('project_password'), input_setter_by_name('project_password'))
    project_password_confirm = property(input_getter_by_name('project_password_confirm'), input_setter_by_name('project_password_confirm'))
    # Azure
    project_subscription_id = property(input_getter_by_name('project_subscription_id'), input_setter_by_name('project_subscription_id'))
    # GCE
    project_email_address = property(input_getter_by_name('project_email_address'), input_setter_by_name('project_email_address'))

    @property
    def project_ssh_password_clear_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['project_ssh_password_clear_btn']))

    @property
    def project_ssh_key_unlock_clear_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['project_ssh_key_unlock_clear_btn']))

    @property
    def project_vault_password_clear_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['project_vault_password_clear_btn']))

    @property
    def owner_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['owner_help']))

    @property
    def kind_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['kind_help']))

    @property
    def login_method_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['login_method_help']))

    @property
    def project_ssh_key_data_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['project_ssh_key_data_help']))

    @property
    def project_subscription_id_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['project_subscription_id_help']))

    @property
    def project_email_address_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['project_email_address_help']))


class Project_Edit_Page(Project_Create_Page):
    _tab_title = "Projects"
    _related = Project_Create_Page._related
    _related.update({
        'activity_stream': 'Project_Activity_Page',
    })

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match object name'''
        return self.name

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))


class Project_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Projects"
    _related = {
        'close': 'Project_Edit_Page',
    }
