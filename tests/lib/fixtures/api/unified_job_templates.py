import pytest


@pytest.fixture(params=('inventory_source', 'job_template', 'project', 'workflow_job_template'))
def unified_job_template(request, factories):
    return getattr(factories, request.param)()
