import logging
import json

from towerkit import utils
import towerkit.tower.inventory
import towerkit.exceptions
import fauxfactory
import pytest

from tests.api import Base_Api_Test


log = logging.getLogger(__name__)


@pytest.fixture(scope="function")
def missing_field_survey_specs(request):
    """Returns a list of survey_spec's which should fail to post."""
    return [dict(),
            dict(description=fauxfactory.gen_utf8(),
                 spec=[dict(required=False,
                            question_name="Enter your email &mdash; &euro;",
                            variable="submitter_email",
                            type="text",)]),
            dict(name=fauxfactory.gen_utf8(),
                 spec=[dict(required=False,
                            question_name="Enter your email &mdash; &euro;",
                            variable="submitter_email",
                            type="text",)]),
            dict(name=fauxfactory.gen_utf8(),
                 description=fauxfactory.gen_utf8()),
            dict(name=fauxfactory.gen_utf8(),
                 description=fauxfactory.gen_utf8(),
                 spec=[])]


@pytest.mark.api
@pytest.mark.skip_selenium
@pytest.mark.destructive
class Test_Job_Template_Surveys(Base_Api_Test):
    """Test job_template surveys"""

    pytestmark = pytest.mark.usefixtures('authtoken', 'install_enterprise_license_unlimited')

    @pytest.mark.parametrize("launch_time_vars", [
        "{'non_survey_variable': false, 'submitter_email': 'sample_email@maffenmox.edu'}",
        "---\nnon_survey_variable: false\nsubmitter_email: sample_email@maffenmox.edu"
    ], ids=['json', 'yaml'])
    def test_launch_with_survey_and_excluded_variables_in_payload(self, job_template, optional_survey_spec_without_defaults,
            launch_time_vars):
        """Tests that when ask_variables_at_launch is disabled that only survey variables are
        received and make it to our job. Here, "submitter_email" is our only survey variable.
        """
        job_template.add_survey(spec=optional_survey_spec_without_defaults)
        assert not job_template.ask_variables_on_launch

        # launch JT with launch-time variables
        payload = dict(extra_vars=launch_time_vars)
        job = job_template.launch(payload).wait_until_completed()
        assert job.is_successful, "Job unsuccessful - %s." % job

        launch_time_vars = utils.load_json_or_yaml(launch_time_vars)
        job_extra_vars = json.loads(job.extra_vars)

        # assert non-survey variables excluded
        expected_job_vars = dict(submitter_email=launch_time_vars['submitter_email'])
        assert job_extra_vars == expected_job_vars, \
            "Unexpected job extra_vars returned."

    def test_post_with_missing_fields(self, job_template_ping, missing_field_survey_specs):
        """Verify the API does not allow survey creation when missing any or all
        of the spec, name, or description fields.
        """
        job_template_ping.patch(survey_enabled=True)

        # assert failure on post
        for payload in missing_field_survey_specs:
            with pytest.raises(towerkit.exceptions.BadRequest):
                job_template_ping.get_related('survey_spec').post(payload)

    def test_post_with_empty_name(self, job_template_ping):
        """Verify the API allows a survey_spec with an empty name and description"""
        job_template_ping.patch(survey_enabled=True)
        payload = dict(name='',
                       description='',
                       spec=[dict(required=False,
                                  question_name=fauxfactory.gen_utf8(),
                                  question_description=fauxfactory.gen_utf8(),
                                  variable="submitter_email",
                                  type="text",)])

        # assert successful post
        job_template_ping.get_related('survey_spec').post(payload)

    def test_post_multiple(self, job_template_ping, optional_survey_spec, required_survey_spec):
        """Verify the API allows posting survey_spec multiple times."""
        # post a survey
        job_template_ping.add_survey(spec=optional_survey_spec)
        survey_spec = job_template_ping.get_related('survey_spec')
        assert survey_spec.spec == optional_survey_spec

        # post another survey
        job_template_ping.add_survey(spec=required_survey_spec)
        # update resource
        survey_spec.get()
        assert survey_spec.spec == required_survey_spec

    def test_launch_survey_enabled(self, job_template_ping, required_survey_spec):
        """Assess launch_pg.survey_enabled behaves as expected."""
        # check that survey_enabled is false by default
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True even though JT survey_enabled is False \
            and no survey given."

        # check that survey_enabled is false when enabled on JT but no survey created
        job_template_ping.patch(survey_enabled=True)
        launch_pg = job_template_ping.get_related("launch")
        assert not launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is True with JT survey_enabled as True \
            and no survey given."

        # check that survey_enabled is true when enabled on JT and survey created
        survey_spec = job_template_ping.get_related('survey_spec')
        survey_spec.post(required_survey_spec)
        launch_pg = job_template_ping.get_related("launch")
        assert launch_pg.survey_enabled, \
            "launch_pg.survey_enabled is False even though JT survey_enabled is True \
            and valid survey posted."

    def test_launch_with_optional_survey_spec(self, job_template_ping, optional_survey_spec):
        """Verify launch_pg attributes with an optional survey spec and job extra_vars."""
        # post a survey
        job_template_ping.add_survey(spec=optional_survey_spec)
        survey_pg = job_template_ping.get_related('survey_spec')

        # assess launch_pg values
        launch_pg = job_template_ping.get_related('launch')
        assert launch_pg.can_start_without_user_input
        assert launch_pg.variables_needed_to_start == []

        # launch the job_template and assess results
        job_pg = job_template_ping.launch().wait_until_completed()
        assert job_pg.is_successful, "Job unsuccessful - %s" % job_pg

        # format job extra_vars
        try:
            job_extra_vars = json.loads(job_pg.extra_vars)
        except ValueError:
            job_extra_vars = {}

        # find expected job extra_vars from survey
        survey_extra_vars = dict((question['variable'], question['default'])
                                 for question in survey_pg.spec
                                 if question.get('required', False) is False and
                                 question.get('default') not in (None, ''))

        # assert expected job extra_vars
        assert set(job_extra_vars) == set(survey_extra_vars)
