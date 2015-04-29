import pytest
import json
import common.utils


@pytest.fixture(scope="function")
def ad_hoc_ping(request, api_ad_hoc_commands_pg, inventory, ssh_credential):
    '''
    Launch an ad_hoc ping command and return the job resource.
    '''
    ad_hoc_commands_pg = api_ad_hoc_commands_pg.get()
    payload = dict(job_type="run",
                   inventory=inventory.id,
                   credential=ssh_credential.id,
                   module_name="ping")

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
