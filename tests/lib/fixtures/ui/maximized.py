import pytest


@pytest.fixture
def maximized(mozwebqa):
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
    return maximized


@pytest.fixture
def window_laptop(mozwebqa):
    '''
    Set window size and position to a typical laptop resolution (1280x720)
    '''
    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(1280, 720)
    return True


@pytest.fixture
def window_mobile(mozwebqa):
    '''
    Set window size and position to a typical mobile resolution (1136x640)
    '''
    mozwebqa.selenium.set_window_position(0, 0)
    mozwebqa.selenium.set_window_size(1136, 640)
    return True
