import pytest


@pytest.fixture(params=('v2_inventory_source', 'v2_job_template', 'v2_project', 'v2_workflow_job_template'))
def v2_unified_job_template(request, factories):
    return getattr(factories, request.param)()
