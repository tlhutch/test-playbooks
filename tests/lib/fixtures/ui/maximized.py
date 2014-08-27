import pytest

@pytest.fixture
def maximized(mozwebqa):
    mozwebqa.selenium.maximize_window()
    return True
