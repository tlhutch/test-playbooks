import pytest

@pytest.mark.ui
@pytest.mark.selenium
@pytest.mark.nondestructive
class BaseTestUI(object):

    pytestmark = pytest.mark.usefixtures(
        'install_license_unlimited',
        'maximized_window_size')

