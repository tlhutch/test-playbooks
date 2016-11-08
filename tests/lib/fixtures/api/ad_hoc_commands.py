import pytest


@pytest.fixture(scope="function")
def ad_hoc_ping(request, api_ad_hoc_commands_pg, host, ssh_credential):
    '''
    Launch an ad_hoc ping command and return the job resource.
    '''
    ad_hoc_commands_pg = api_ad_hoc_commands_pg.get()
    payload = dict(inventory=host.inventory,
                   credential=ssh_credential.id,
                   module_name="ping")

    fixture_args = getattr(request.function, 'fixture_args', None)
    for key in ('module_name', 'module_args', 'job_type'):
        if fixture_args and key in fixture_args.kwargs:
            payload[key] = fixture_args.kwargs[key]

    return ad_hoc_commands_pg.post(payload)


@pytest.fixture(scope="function")
def ad_hoc_with_status_pending(pause_awx_task_system, ad_hoc_ping):
    '''
    Wait for ad_hoc_ping to move from new to queued and return the job.
    '''
    return ad_hoc_ping.wait_until_started()


@pytest.fixture(scope="function")
def ad_hoc_with_status_running(ad_hoc_ping):
    '''
    Wait for ad_hoc_ping to move from queued to running, and return the job.
    '''
    return ad_hoc_ping.wait_until_status('running')


@pytest.fixture(scope="function")
def ad_hoc_with_status_completed(ad_hoc_ping):
    '''
    Wait for ad_hoc_ping to finish, and return the job.
    '''
    return ad_hoc_ping.wait_until_completed()


@pytest.fixture(scope="function")
def ad_hoc_module_name_choices(api_ad_hoc_commands_pg):
    '''
    Returns the list of module_names from api/v1/ad_hoc_commands OPTIONS.
    '''
    def func():
        options_json = api_ad_hoc_commands_pg.options().json
        return options_json["actions"]["POST"]["module_name"]['choices']
    return func
