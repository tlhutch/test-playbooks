import pytest
import datetime

from towerkit import utils


@pytest.fixture(scope="function")
def job_with_status_completed(job_template_ping):
    """Launch job_template_ping and return the job resource."""
    return job_template_ping.launch().wait_until_completed()


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
    return job_template_with_extra_vars.launch()


@pytest.fixture(scope="function")
def job_with_ssh_connection(job_template_with_ssh_connection):
    """Launch job_with_ssh_connection and return the job resource."""
    return job_template_with_ssh_connection.launch()


@pytest.fixture
def wait_for_jobs(v2):
    def fn(jobs, status='successful', interval=5, timeout=120, **kwargs):
        return utils.poll_until(lambda: v2.unified_jobs.get(id__in=','.join([str(j.id) for j in
                    jobs]), status=status, **kwargs).count == len(jobs), interval=interval, timeout=timeout)
    return fn


@pytest.fixture
def do_all_jobs_overlap():
    def fn(jobs):
        return max(
            datetime.datetime.strptime(job.started, '%Y-%m-%dT%H:%M:%S.%fZ') for job in jobs
        ) < min(
            datetime.datetime.strptime(job.finished, '%Y-%m-%dT%H:%M:%S.%fZ') for job in jobs
        )
    return fn
