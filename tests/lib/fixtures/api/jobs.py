import pytest


@pytest.fixture(scope="function")
def job_with_status_completed(request, job_template_ping):
    '''
    Launch job_template_ping and return a job resource.
    '''
    return job_template_ping.launch().wait_until_completed()


@pytest.fixture(scope="function")
def scan_job_with_status_completed(request, scan_job_template):
    '''
    Launch scan_job_template and return a job resource.
    '''
    return scan_job_template.launch().wait_until_completed()


@pytest.fixture(scope="function")
def files_scan_job_with_status_completed(request, files_scan_job_template):
    '''
    Launch files_scan_job_template and return a job resource.
    '''
    return files_scan_job_template.launch().wait_until_completed()


@pytest.fixture(scope="function")
def api_jobs_options_json(request, authtoken, api_jobs_pg):
    '''Return job statuses from OPTIONS'''
    return api_jobs_pg.options().json


@pytest.fixture(scope="function")
def job_status_choices(request, api_jobs_options_json):
    '''Return job statuses from OPTIONS'''
    return dict(api_jobs_options_json['actions']['GET']['status']['choices'])


@pytest.fixture(scope="function")
def job_type_choices(request, api_jobs_options_json):
    '''Return job statuses from OPTIONS'''
    return dict(api_jobs_options_json['actions']['GET']['job_type']['choices'])


@pytest.fixture(scope="function")
def job_launch_type_choices(request, api_jobs_options_json):
    '''Return job statuses from OPTIONS'''
    return dict(api_jobs_options_json['actions']['GET']['launch_type']['choices'])


@pytest.fixture(scope="function")
def job_extra_vars_dict():
    return dict(Flaff=True, Moffey=False, Maffey=True)


@pytest.fixture(scope="function")
def job_with_extra_vars(request, job_template_with_extra_vars, job_extra_vars_dict):
    '''
    Launch the job_template_extra_vars and return a job resource.  Extra vars
    are passed in with the POST request to the launch endpoint.
    '''
    # Locate job_template launch page
    launch_pg = job_template_with_extra_vars.get_related('launch')

    # Launch with additional extra_vars
    payload = dict(extra_vars=job_extra_vars_dict)
    result = launch_pg.post(payload)

    # find and return specific job_pg
    jobs_pg = job_template_with_extra_vars.get_related('jobs', id=result.json['job'])
    assert jobs_pg.count == 1, "Unexpected number of jobs returned (%s != 1)" % jobs_pg.count
    return jobs_pg.results[0]
