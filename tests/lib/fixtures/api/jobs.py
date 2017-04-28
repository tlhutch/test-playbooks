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


@pytest.fixture(scope="function", params=['json_launch_time_vars', 'yaml_launch_time_vars'])
def launch_time_extra_vars(request):
    return request.getfuncargvalue(request.param)


@pytest.fixture(scope="function")
def json_launch_time_vars():
    return "{'job_var': 0, 'intersection': 'launch-time'}"


@pytest.fixture(scope="function")
def yaml_launch_time_vars():
    return "---\njob_var: 0\nintersection: launch-time"


@pytest.fixture(scope="function")
def job_with_extra_vars(job_template_with_extra_vars):
    """Launch job_template_extra_vars and return the job resource."""
    return job_template_with_extra_vars.launch().wait_until_completed()


@pytest.fixture(scope="function")
def job_with_ssh_connection(job_template_with_ssh_connection):
    """Launch job_with_ssh_connection and return the job resource."""
    return job_template_with_ssh_connection.launch()
