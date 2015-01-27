from selenium.webdriver.common.by import By
from common.ui.pages import MainTab_Page
from common.ui.pages.forms import Form_Page, input_getter_by_name, input_setter_by_name
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button, Select_Button  # NOQA
from common.ui.pages.regions.dialogs import Prompt_Dialog  # NOQA
from common.ui.pages.regions.lists import List_Region  # NOQA


class Credentials_Page(MainTab_Page):
    '''Describes credentials page'''
    _tab_title = "Credentials"
    _related = {
        'add': 'Credential_Create_Page',
        'edit': 'Credential_Edit_Page',
        'delete': 'Prompt_Dialog',
        'activity_stream': 'Credentials_Activity_Page',
    }
    _locators = {
        'table': (By.CSS_SELECTOR, '#credentials_table'),
        'pagination': (By.CSS_SELECTOR, '#credential-pagination'),
    }


class Credentials_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for all credentials'''
    _tab_title = "Credentials"
    _related = {
        'close': 'Credentials_Page',
    }


class Credential_Create_Page(Form_Page):
    '''Describes the credentials create page'''
    _tab_title = "Credentials"
    _breadcrumb_title = 'Create Credential'
    _related = {
        'save': 'Credentials_Page',
    }
    _locators = {
        'form': (By.CSS_SELECTOR, '#credential_form'),
        'name': (By.CSS_SELECTOR, '#credential_name'),
        'description': (By.CSS_SELECTOR, '#credential_description'),
        'owner': (By.CSS_SELECTOR, "input[name='owner']"),
        'user_btn': (By.CSS_SELECTOR, '#user-lookup-btn'),
        'user_username': (By.CSS_SELECTOR, "input[name='user_username']"),
        'team_btn': (By.CSS_SELECTOR, '#team-lookup-btn'),
        'team_name': (By.CSS_SELECTOR, "input[name='team_name']"),
        'credential_kind': (By.CSS_SELECTOR, '#credential_kind'),
        'login_method': (By.CSS_SELECTOR, "input[name='login_method']"),
        # ssh_username
        'credential_username': (By.CSS_SELECTOR, '#credential_username'),
        # ssh_password
        'credential_ssh_password_ask': (By.CSS_SELECTOR, '#credential_ssh_password_ask_chbox'),
        'credential_ssh_password': (By.CSS_SELECTOR, '#credential_ssh_password'),
        'credential_ssh_password_confirm': (By.CSS_SELECTOR, '#credential_ssh_password_confirm'),
        'credential_ssh_password_clear_btn': (By.CSS_SELECTOR, '#credential_ssh_password_clear_btn'),
        # key_data
        'credential_ssh_key_data': (By.CSS_SELECTOR, '#credential_ssh_key_data'),
        # key_data_unlock
        'credential_ssh_key_unlock_ask': (By.CSS_SELECTOR, '#credential_ssh_key_unlock_ask_chbox'),
        'credential_ssh_key_unlock': (By.CSS_SELECTOR, '#credential_ssh_key_unlock'),
        'credential_ssh_key_unlock_confirm': (By.CSS_SELECTOR, '#credential_ssh_key_unlock_confirm'),
        'credential_ssh_key_unlock_clear_btn': (By.CSS_SELECTOR, '#credential_ssh_key_unlock_clear_btn'),
        # vault_password
        'credential_vault_password_ask': (By.CSS_SELECTOR, '#credential_vault_password_ask_chbox'),
        'credential_vault_password': (By.CSS_SELECTOR, '#credential_vault_password'),
        'credential_vault_password_confirm': (By.CSS_SELECTOR, '#credential_vault_password_confirm'),
        'credential_vault_password_clear_btn': (By.CSS_SELECTOR, '#credential_vault_password_clear_btn'),
        # vCenter
        'credential_host': (By.CSS_SELECTOR, '#credential_host'),
        'credential_password': (By.CSS_SELECTOR, '#credential_password'),
        'credential_password_confirm': (By.CSS_SELECTOR, '#credential_password_confirm'),
        # Azure
        'credential_subscription_id': (By.CSS_SELECTOR, '#credential_subscription_id'),
        # GCE
        'credential_email_address': (By.CSS_SELECTOR, '#credential_email_address'),
        # Help buttons
        'owner_help': (By.CSS_SELECTOR, '#awp-owner'),
        'kind_help': (By.CSS_SELECTOR, '#awp-kind'),
        'credential_ssh_key_data_help': (By.CSS_SELECTOR, '#awp-ssh_key_data'),
        'login_method_help': (By.CSS_SELECTOR, '#awp-login_method'),
        'credential_subscription_id_help': (By.CSS_SELECTOR, '#awp-subscription_id'),
        'credential_email_address_help': (By.CSS_SELECTOR, '#awp-email_address'),
        # Form Buttons
        'save_btn': (By.CSS_SELECTOR, '#credential_save_btn'),
        'reset_btn': (By.CSS_SELECTOR, '#credential_reset_btn'),
    }

    name = property(input_getter_by_name('name'), input_setter_by_name('name'))
    description = property(input_getter_by_name('description'), input_setter_by_name('description'))
    owner = property(input_getter_by_name('owner'), input_setter_by_name('owner'))
    user_username = property(input_getter_by_name('user_username'), input_setter_by_name('user_username'))
    team_name = property(input_getter_by_name('team_name'), input_setter_by_name('team_name'))
    credential_kind = property(input_getter_by_name('credential_kind'), input_setter_by_name('credential_kind'))
    login_method = property(input_getter_by_name('login_method'), input_setter_by_name('login_method'))
    # username
    credential_username = property(input_getter_by_name('credential_username'), input_setter_by_name('credential_username'))
    # ssh_password
    credential_ssh_password_ask = property(input_getter_by_name('credential_ssh_password_ask'), input_setter_by_name('credential_ssh_password_ask'))
    credential_ssh_password = property(input_getter_by_name('credential_ssh_password'), input_setter_by_name('credential_ssh_password'))
    credential_ssh_password_confirm = property(input_getter_by_name('credential_ssh_password_confirm'), input_setter_by_name('credential_ssh_password_confirm'))
    # key_data
    credential_ssh_key_data = property(input_getter_by_name('credential_ssh_key_data'), input_setter_by_name('credential_ssh_key_data'))
    # key_unlock
    credential_ssh_key_unlock_ask = property(input_getter_by_name('credential_ssh_key_unlock_ask'), input_setter_by_name('credential_ssh_key_unlock_ask'))
    credential_ssh_key_unlock = property(input_getter_by_name('credential_ssh_key_unlock'), input_setter_by_name('credential_ssh_key_unlock'))
    credential_ssh_key_unlock_confirm = property(input_getter_by_name('credential_ssh_key_unlock_confirm'),
                                                 input_setter_by_name('credential_ssh_key_unlock_confirm'))
    # vault
    credential_vault_password_ask = property(input_getter_by_name('credential_vault_password_ask'), input_setter_by_name('credential_vault_password_ask'))
    credential_vault_password = property(input_getter_by_name('credential_vault_password'), input_setter_by_name('credential_vault_password'))
    credential_vault_password_confirm = property(input_getter_by_name('credential_vault_password_confirm'),
                                                 input_setter_by_name('credential_vault_password_confirm'))
    # vCenter
    credential_host = property(input_getter_by_name('credential_host'), input_setter_by_name('credential_host'))
    credential_password = property(input_getter_by_name('credential_password'), input_setter_by_name('credential_password'))
    credential_password_confirm = property(input_getter_by_name('credential_password_confirm'), input_setter_by_name('credential_password_confirm'))
    # Azure
    credential_subscription_id = property(input_getter_by_name('credential_subscription_id'), input_setter_by_name('credential_subscription_id'))
    # GCE
    credential_email_address = property(input_getter_by_name('credential_email_address'), input_setter_by_name('credential_email_address'))

    @property
    def credential_ssh_password_clear_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['credential_ssh_password_clear_btn']))

    @property
    def credential_ssh_key_unlock_clear_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['credential_ssh_key_unlock_clear_btn']))

    @property
    def credential_vault_password_clear_btn(self):
        return Base_Button(self.testsetup, _root_element=self.find_element(*self._locators['credential_vault_password_clear_btn']))

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
    def credential_ssh_key_data_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['credential_ssh_key_data_help']))

    @property
    def credential_subscription_id_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['credential_subscription_id_help']))

    @property
    def credential_email_address_help(self):
        return Help_Button(self.testsetup, _root_element=self.find_element(*self._locators['credential_email_address_help']))


class Credential_Edit_Page(Credential_Create_Page):
    _tab_title = "Credentials"
    _related = Credential_Create_Page._related
    _related.update({
        'activity_stream': 'Credential_Activity_Page',
    })

    @property
    def _breadcrumb_title(self):
        '''The breadcrumb title should always match object name'''
        return self.name

    @property
    def activity_stream_btn(self):
        return Activity_Stream_Button(self.testsetup, _item_class=self.get_related('activity_stream'))


class Credential_Activity_Page(Activity_Stream_Region):
    '''Activity stream page for a single organizations'''
    _tab_title = "Credentials"
    _related = {
        'close': 'Credential_Edit_Page',
    }
