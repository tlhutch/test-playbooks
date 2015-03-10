import pytest


@pytest.fixture(scope="function")
def job_with_status_completed(request, job_template_ping):
    '''
    Launch job_template_ping and return a job resource.
    '''
    job_pg = job_template_ping.launch()
    return job_pg.wait_until_completed()


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
