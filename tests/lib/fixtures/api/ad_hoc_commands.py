import pytest


@pytest.fixture(scope="function")
def ad_hoc_ping(request, api_ad_hoc_commands_pg, inventory, ssh_credential):
    '''
    Launch an ad_hoc ping command and return the job resource.
    '''
    ad_hoc_commands_pg = api_ad_hoc_commands_pg.get()
    payload = dict(inventory=inventory.id,
                   credential=ssh_credential.id,
                   module_name="ping")

    # optionally override module_name
    fixture_args = getattr(request.function, 'fixture_args', None)
    if fixture_args and fixture_args.kwargs.get('module_name', False):
        payload['module_name'] = fixture_args.kwargs['module_name']

    # optionally override module_args
    if fixture_args and fixture_args.kwargs.get('module_args', False):
        payload['module_args'] = fixture_args.kwargs['module_args']

    return ad_hoc_commands_pg.post(payload)


@pytest.fixture(scope="function")
def ad_hoc_with_status_pending(ad_hoc_ping):
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
def ad_hoc_options_json(request, authtoken, api_ad_hoc_commands_pg):
    '''
    Returns api/v1/ad_hoc_commands OPTIONS.
    '''
    return api_ad_hoc_commands_pg.options().json


@pytest.fixture(scope="function")
def ad_hoc_module_name_choices(ad_hoc_options_json):
    '''
    Returns the list of module_names from api/v1/ad_hoc_commands OPTIONS.
    '''
    return dict(ad_hoc_options_json["actions"]["POST"]["module_name"]['choices'])
