import pytest
import fauxfactory


@pytest.fixture
def workflow_job_template(factories):
    return factories.workflow_job_template()


@pytest.fixture(scope="function", params=['workflow_job_template_with_json_vars', 'workflow_job_template_with_yaml_vars'])
def workflow_job_template_with_extra_vars(request):
    """WFJT with a set of extra_vars"""
    return request.getfixturevalue(request.param)


@pytest.fixture
def workflow_job_template_with_json_vars(factories):
    """WFJT with a set of JSON extra_vars."""
    return factories.workflow_job_template(description="WFJT with extra_vars - {0}.".format(fauxfactory.gen_utf8()),
                                           extra_vars='{"wfjt_var": 1.0, "intersection": "wfjt"}')


@pytest.fixture
def workflow_job_template_with_yaml_vars(factories):
    """WFJT with a set of YAML extra_vars."""
    return factories.workflow_job_template(description="WFJT with extra_vars - {0}.".format(fauxfactory.gen_utf8()),
                                           extra_vars="---\nwfjt_var: 1.0\nintersection: wfjt")
