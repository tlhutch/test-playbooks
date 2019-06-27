import pytest

@pytest.fixture(scope='session', autouse=True)
def session_install_enterprise_license_unlimited(apply_license, class_subrequest):
    """Apply an enterprise license to entire session when tests are run in tests/api.

    Locate this fixture in tests/api/conftest.py such that it is only applied when the session
    includes collecting tests in tests/api.

    That means that collecting tests in tests/api is mutually exclusive with collecting tests in
    tests/license.
    """
    with apply_license('enterprise', request=class_subrequest):
        yield
