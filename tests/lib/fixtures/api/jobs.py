import pytest


@pytest.fixture(scope="function")
def job_with_status_completed(job_template_ping):
    """Launch job_template_ping and return the job resource."""
    return job_template_ping.launch().wait_until_completed()


@pytest.fixture(scope="function")
def scan_job_with_status_completed(scan_job_template):
    """Launch scan_job_template and return the job resource."""
    return scan_job_template.launch().wait_until_completed()


@pytest.fixture(scope="function")
def files_scan_job_with_status_completed(files_scan_job_template):
    """Launch files_scan_job_template and return the job resource."""
    return files_scan_job_template.launch().wait_until_completed()


@pytest.fixture(scope="function")
def job_extra_vars_dict():
    return dict(Flaff=True, Moffey=False, Maffey=True, intersection="job")


@pytest.fixture(scope="function")
def job_with_extra_vars(job_template_with_extra_vars, job_extra_vars_dict):
    """Launch job_template_extra_vars and return the job resource."""
    # Supply extra variables at launch time
    payload = dict(extra_vars=job_extra_vars_dict)
    return job_template_with_extra_vars.launch(payload)


@pytest.fixture(scope="function")
def job_with_ssh_connection(job_template_with_ssh_connection):
    """Launch job_with_ssh_connection and return the job resource."""
    return job_template_with_ssh_connection.launch()
