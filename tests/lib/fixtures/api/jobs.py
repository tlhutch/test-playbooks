import pytest
import datetime
import itertools

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
        def overlap(start1, end1, start2, end2):
            """Does the range (start1, end1) overlap with (start2, end2)?"""
            return end1 >= start2 and end2 >= start1

        for (j1, j2) in list(itertools.combinations(jobs, 2)):
            if not overlap(datetime.datetime.strptime(j1.started, '%Y-%m-%dT%H:%M:%S.%fZ'),
                           datetime.datetime.strptime(j1.finished, '%Y-%m-%dT%H:%M:%S.%fZ'),
                           datetime.datetime.strptime(j2.started, '%Y-%m-%dT%H:%M:%S.%fZ'),
                           datetime.datetime.strptime(j2.finished, '%Y-%m-%dT%H:%M:%S.%fZ')):
                return False
        return True
    return fn
