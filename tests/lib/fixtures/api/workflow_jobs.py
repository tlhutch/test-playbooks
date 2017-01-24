import pytest


@pytest.fixture
def workflow_job_with_status_completed(request, workflow_job_template):
    workflow_job_template.launch().wait_until_completed()
