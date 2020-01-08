# -*- coding: utf-8 -*-
import pytest
import datetime
import yaml

from awxkit import utils


@pytest.fixture(scope="function")
def job_with_status_completed(job_template_ping):
    """Launch job_template_ping and return the job resource."""
    return job_template_ping.launch().wait_until_completed()


@pytest.fixture(scope="function", params=['json_launch_time_vars', 'yaml_launch_time_vars'])
def launch_time_extra_vars(request):
    return request.getfixturevalue(request.param)


@pytest.fixture(scope="function")
def json_launch_time_vars():
    return "{'job_var': 0, 'intersection': 'launch-time'}"


@pytest.fixture(scope="function")
def yaml_launch_time_vars():
    return "---\njob_var: 0\nintersection: launch-time"


@pytest.fixture
def artifacts_from_stats_playbook():
    # data from the test_set_stats.yml playbook verbatum
    return yaml.load('\n'.join([
        "---",
        "string: 'abc'",
        "integer: 123",
        "float: 1.0",
        "unicode: '竳䙭韽'",
        "boolean: true",
        "none: null",
        "list:",
        "  - 'abc'",
        "  - 123",
        "  - 1.0",
        "  - '竳䙭韽'",
        "  - true",
        "  - null",
        "  - []",
        "  - {}",
        "object:",
        "  string: 'abc'",
        "  integer: 123",
        "  float: 1.0",
        "  unicode: '竳䙭韽'",
        "  boolean: true",
        "  none: null",
        "  list: []",
        "  object: {}",
        "empty_list: []",
        "empty_object: {}"]), Loader=yaml.SafeLoader)


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
    def fn(jobs, error_margin=0):
        started_series = [datetime.datetime.strptime(job.started, '%Y-%m-%dT%H:%M:%S.%fZ') for job in jobs]
        if None in started_series:
            return False  # if a job hasn't started yet, we can't say they overlap
        finished_series = [
            datetime.datetime.strptime(job.finished, '%Y-%m-%dT%H:%M:%S.%fZ') for job in jobs if job.finished
        ]
        if finished_series == []:
            return True  # all jobs have started but none have finished, so we can say they overlap
        return max(started_series) < min(finished_series) + datetime.timedelta(seconds=error_margin)
    return fn
