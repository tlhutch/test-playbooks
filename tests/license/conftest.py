import pytest

@pytest.fixture(scope='module')
def no_license(apply_license, module_subrequest):
    with apply_license(None, request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_legacy_license(apply_license, module_subrequest):
    with apply_license('legacy', request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_basic_license(apply_license, module_subrequest):
    with apply_license('basic', request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_enterprise_license(apply_license, module_subrequest):
    with apply_license('enterprise', request=module_subrequest):
        yield


@pytest.fixture(scope='module')
def install_enterprise_license_unlimited(apply_license, module_subrequest):
    with apply_license('enterprise', request=module_subrequest):
        yield
