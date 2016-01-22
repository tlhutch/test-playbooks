import logging
import pytest


log = logging.getLogger(__name__)


@pytest.fixture(scope="function", params=['maximized', 'laptop', 'mobile', 'small_mobile', 'hdtv'])
def window_size(request):
    return request.getfuncargvalue(request.param + '_window_size')


@pytest.fixture
def maximized_window_size(mozwebqa):
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
def laptop_window_size(mozwebqa):
    '''
    Set window size and position to a typical laptop resolution (1280x720)
    '''
    log.debug("Calling fixture window_laptop")
    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(1280, 720)

    return True


@pytest.fixture
def mobile_window_size(mozwebqa):
    '''
    Set window size and position to a typical mobile resolution (1024x768)
    '''
    log.debug("Calling fixture window_mobile")
    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(1024, 768)

    return True


@pytest.fixture
def small_mobile_window_size(mozwebqa):
    """Set window size to a typical small mobile resolution (800x600)
    """
    log.debug('Calling fixture window_small_mobile')

    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(800, 600)

    return True


@pytest.fixture
def hdtv_window_size(mozwebqa):
    """Set window size to a typical hdtv resolution (1366x768)
    """
    log.debug('Calling fixture window_hdtv')

    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(1366, 768)

    return True
