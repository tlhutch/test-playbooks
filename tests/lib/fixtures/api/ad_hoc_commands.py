import pytest


@pytest.fixture(scope="function")
def ad_hoc_command(request, factories, host, ssh_credential):
    kwargs = dict(inventory=host.ds.inventory, credential=ssh_credential)
    fixture_args = getattr(request.function, 'fixture_args', None)
    if fixture_args:
        for key in ('module_name', 'module_args', 'job_type'):
            if key in fixture_args.kwargs:
                kwargs[key] = fixture_args.kwargs[key]

    return factories.ad_hoc_command(**kwargs)


@pytest.fixture(scope="function")
def ad_hoc_with_status_pending(pause_awx_task_system, ad_hoc_command):
    """Wait for ad_hoc_command to move from new to queued and return the job."""
    return ad_hoc_command.wait_until_started()


@pytest.fixture(scope="function")
def ad_hoc_with_status_completed(ad_hoc_command):
    return ad_hoc_command.wait_until_completed()


@pytest.fixture(scope="function")
def ad_hoc_module_name_choices(api_ad_hoc_commands_pg):
    """Returns the list of module_names from api/v1/ad_hoc_commands OPTIONS."""
    def func():
        options = api_ad_hoc_commands_pg.options()
        return options.actions.POST.module_name.choices
    return func
