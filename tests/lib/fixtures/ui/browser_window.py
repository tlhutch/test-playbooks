import logging
import pytest


log = logging.getLogger(__name__)


@pytest.fixture
def maximized(mozwebqa):
    log.debug("Calling fixture maximized")
    if mozwebqa.selenium.name == 'chrome':
        '''Chrome doesn't seem to handle maximize properly'''
        (width, height) = mozwebqa.selenium.execute_script("return [screen.width, screen.height];")
        mozwebqa.selenium.set_window_position(0, 0)
        mozwebqa.selenium.set_window_size(width, height)
    else:
        '''For everything else, just perform a normal maximize_window()'''
        mozwebqa.selenium.maximize_window()
    return True


@pytest.fixture
def window_maximized(mozwebqa, maximized):
    '''
    Set window size and position to the minimum
    '''
    log.debug("Calling fixture window_maximized")
    return maximized


@pytest.fixture
def window_laptop(mozwebqa):
    '''
    Set window size and position to a typical laptop resolution (1280x720)
    '''
    log.debug("Calling fixture window_laptop")
    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(1280, 720)
    return True


@pytest.fixture
def window_mobile(mozwebqa):
    '''
    Set window size and position to a typical mobile resolution (1024x768)
    '''
    log.debug("Calling fixture window_mobile")
    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(1024, 768)
    return True
