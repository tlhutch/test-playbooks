def pytest_addoption(parser):
    group = parser.getgroup('selenium', 'selenium')
    group._addoption('--highlight',
                     action='store_true',
                     dest='highlight',
                     default=False,
                     help='whether to turn on highlighting of elements')


def highlight(element):
    """Highlights (blinks) a Webdriver element.
        In pure javascript, as suggested by https://github.com/alp82.
    """
    driver = element._parent
    driver.execute_script("""
        element = arguments[0];
        highlight_bg = arguments[1];
        highlight_outline = arguments[2];

        original_bg = element.style.backgroundColor;
        original_outline = element.style.outline;

        element.style.backgroundColor = highlight_bg;
        element.style.outline = highlight_outline;

        setTimeout(function(){
            element.style.backgroundColor = original_bg;
            element.style.outline = original_outline;
        }, 10);
        """, element, "#FFFFCC", "#8f8 solid 1px")


def pytest_configure(config):
    from selenium.webdriver.remote.webelement import WebElement

    def _execute(self, command, params=None):
        highlight(self)
        return self._old_execute(command, params)

    # Let's add highlight as a method to WebDriver so we can call it arbitrarily
    WebElement.highlight = highlight

    if (config.option.highlight):
        WebElement._old_execute = WebElement._execute
        WebElement._execute = _execute
