import pytest


@pytest.fixture
def workflow_job_template(factories):
    return factories.workflow_job_template()
