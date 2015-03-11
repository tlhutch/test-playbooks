import pytest


@pytest.fixture(scope="function", params=['cleanup_jobs', 'cleanup_deleted', 'cleanup_activitystream'])
def system_job_template(request, api_system_job_templates_pg):
    return request.getfuncargvalue(request.param + '_template')


@pytest.fixture(scope="function")
def cleanup_jobs_template(request, api_system_job_templates_pg):
    '''
    Return a System_Job_Template object representing the 'cleanup_jobs' system
    job template.
    '''
    matches = api_system_job_templates_pg.get(job_type='cleanup_jobs')
    assert matches.count == 1, "Unexpected number of results (%s) when querying " \
        "for system_job_template job_type:cleanup_jobs" % matches.count
    return matches.results[0]


@pytest.fixture(scope="function")
def cleanup_deleted_template(request, api_system_job_templates_pg):
    '''
    Return a System_Job_Template object representing the 'cleanup_deleted' system
    job template.
    '''
    matches = api_system_job_templates_pg.get(job_type='cleanup_deleted')
    assert matches.count == 1, "Unexpected number of results (%s) when querying " \
        "for system_job_template job_type:cleanup_deleted" % matches.count
    return matches.results[0]


@pytest.fixture(scope="function")
def cleanup_activitystream_template(request, api_system_job_templates_pg):
    '''
    Return a System_Job_Template object representing the 'cleanup_activitystream'
    system job template.
    '''
    matches = api_system_job_templates_pg.get(job_type='cleanup_activitystream')
    assert matches.count == 1, "Unexpected number of results (%s) when querying " \
        "for system_job_template job_type:cleanup_activitystream" % matches.count
    return matches.results[0]
