import pytest


@pytest.fixture
def workflow_job_template(request, factories):
    wfjt = factories.workflow_job_template()
    request.addfinalizer(wfjt.silent_cleanup)
    return wfjt
