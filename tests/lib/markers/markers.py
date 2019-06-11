"""Register tower-qa custom marks."""

_MARKERS = {
    'ansible_integration':
        'mark for tests that exercise the integration of Ansible Tower with '
        'Ansible Core.',
    'fixture_args(*args, *kwargs)':
        'provide args and kwargs to various fixtures on tests/lib/fixtures/',
    'serial':
        'mark for tests that must run serially.',
    'yolo':
        'mark a test to run on yolo.',
}

_PYTEST_ORDERING_MARKERS = {
    'first': 'mark a test to run first.',
    'second': 'mark a test to run second.',
    'second_to_last': 'mark a test to run second to last.',
    'last': 'mark a test to run last.',
}


def pytest_configure(config):
    # Register tower-qa related marks
    for mark, description in _MARKERS.items():
        config.addinivalue_line('markers', f'{mark}: {description}')

    # Since we are running pytest with the --strict-markers option we need to
    # register some marks that are not registerd by some plugins such as and
    # pytest-ordering
    for mark, description in _PYTEST_ORDERING_MARKERS.items():
        config.addinivalue_line(
            'markers', f'{mark}: {description} Provided by pytest-ordering.')
