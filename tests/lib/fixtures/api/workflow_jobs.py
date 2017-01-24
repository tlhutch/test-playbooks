import pytest


@pytest.fixture
def workflow_job_with_status_completed(request, workflow_job_template):
    return workflow_job_template.launch().wait_until_completed()
