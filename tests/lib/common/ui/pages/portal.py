from selenium.webdriver.common.by import By
from common.ui.pages import MainTab_Page, BaseRegion, Base
from common.ui.pages.forms import Form_Page, input_getter_by_name, input_setter_by_name
from common.ui.pages.regions.accordion import Accordion_Region, Accordion_Content
from common.ui.pages.regions.stream_container import Activity_Stream_Region
from common.ui.pages.regions.buttons import Activity_Stream_Button, Base_Button, Add_Button, Help_Button, Select_Button  # NOQA
from common.ui.pages.regions.dialogs import Prompt_Dialog  # NOQA
from common.ui.pages.regions.lists import List_Region  # NOQA


class Portal_Page(MainTab_Page):
    _tab_title = "Portal"


class Portal_Page(Base):
    '''Describes portal page'''
    _tab_title = "Portal"
    _related = {}
    _locators = {}
