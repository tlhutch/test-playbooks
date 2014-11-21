'''
Repeat tests a specified number of times.
'''


def pytest_addoption(parser):
    parser.addoption('--repeat', default=None, type='int', metavar='count', help='Run each test the specified number of times')


def pytest_generate_tests(metafunc):
    if metafunc.config.option.repeat is not None:
        for i in range(metafunc.config.option.repeat):
            metafunc.addcall()
