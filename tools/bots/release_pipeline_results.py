#!/usr/bin/env python
# Copyright 2019 Yanis Guenane  <yguenane@redhat.com>
# Author: Yanis Guenane  <yguenane@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from jenkinsapi.jenkins import Jenkins


def generate_message(build, **kwargs):

    BALL_ASSOCIATION = {
        "FAILURE": ":red_ball:",
        "UNSTABLE": ":yellow_ball:",
        "SUCCESS": ":green_ball:",
        "ABORTED": ":grey_ball:",
    }

    release_pipeline_build_id = kwargs.get("release_pipeline_build_id")
    scenario = kwargs.get("scenario")
    platform = kwargs.get("platform")

    if scenario == "openshift":
        if not build:
            return (
                "  * [OpenShift] Something went wrong. Build has not run for Release Pipeline #%s"
                % release_pipeline_build_id
            )
        if build.get_status() == "UNSTABLE":
            return "  * [OpenShift] Build is %s (%s failures) - <%s|Test Report>" % (
                BALL_ASSOCIATION[build.get_status()],
                build.get_resultset()._data["failCount"],
                build.get_result_url().replace("api/python", ""),
            )
        elif build.get_status() == "SUCCESS":
            return "  * [OpenShift] Build is %s - <%s|Test Report>" % (
                BALL_ASSOCIATION[build.get_status()],
                build.get_result_url().replace("api/python", ""),
            )
        else:
            return "  * [OpenShift] Build is %s - <%s|Build URL>" % (
                BALL_ASSOCIATION[build.get_status()],
                build.get_build_url().replace("api/python", ""),
            )

    else:
        if not build:
            return (
                "  * [%s - %s] Something went wrong. Build has not run for Release Pipeline #%s"
                % (platform, scenario, release_pipeline_build_id)
            )
        elif build.get_status() == "UNSTABLE":
            return "  * [%s - %s] Build is %s (%s failures) - <%s|Test Report>" % (
                platform,
                scenario,
                BALL_ASSOCIATION[build.get_status()],
                build.get_resultset()._data["failCount"],
                build.get_result_url().replace("api/python", ""),
            )
        elif build.get_status() == "SUCCESS":
            return "  * [%s - %s] Build is %s - <%s|Test Report>" % (
                platform,
                scenario,
                BALL_ASSOCIATION[build.get_status()],
                build.get_result_url().replace("api/python", ""),
            )
        else:
            return "  * [%s - %s] Build is %s - <%s|Build URL>" % (
                platform,
                scenario,
                BALL_ASSOCIATION[build.get_status()],
                build.get_build_url().replace("api/python", ""),
            )


def get_jenkins_instance():
    return Jenkins(
        os.getenv("JENKINS_URL"),
        username=os.getenv("JENKINS_USERNAME"),
        password=os.getenv("JENKINS_TOKEN"),
    )


def get_tower_version_that_is_being_tested(builds, release_pipeline_build_id):

    first_build_number = builds.get_first_buildnumber()
    last_build_number = builds.get_last_buildnumber()

    for build_id in range(first_build_number, last_build_number + 1)[::-1]:
        try:
            if (
                builds[build_id].get_upstream_build().get_number()
                == release_pipeline_build_id
            ):
                return builds[build_id].get_params()["TOWER_VERSION"]
        except Exception:
            continue


def did_it_run(
    builds,
    scenario,
    tower_version,
    release_pipeline_build_id,
    platform=None,
    ansible_version=None,
):

    first_build_number = builds.get_first_buildnumber()
    last_build_number = builds.get_last_buildnumber()

    for build_id in range(first_build_number, last_build_number + 1)[::-1]:

        build_params = builds[build_id].get_params()
        if scenario == "openshift":
            try:
                current_release_pipeline_id = (
                    builds[build_id].get_upstream_build().get_upstream_build().get_number()
                )
            except Exception:
                continue
            if (
                build_params["TOWER_VERSION"] == tower_version
                and current_release_pipeline_id < release_pipeline_build_id
            ):
                return False
            elif (
                build_params["TOWER_VERSION"] == tower_version
                and current_release_pipeline_id == release_pipeline_build_id
            ):
                return builds[build_id]
        else:
            try:
                current_release_pipeline_id = (
                    builds[build_id]
                    .get_upstream_build()
                    .get_upstream_build()
                    .get_upstream_build()
                    .get_upstream_build()
                    .get_number()
                )
            except Exception:
                continue
            if (
                # build_params["TOWER_VERSION"] == tower_version
                # and build_params["SCENARIO"] == scenario
                # and build_params["PLATFORM"] == platform
                # and build_params["ANSIBLE_VERSION"] == ansible_version
                current_release_pipeline_id < release_pipeline_build_id
            ):
                return False
            elif (
                build_params["TOWER_VERSION"] == tower_version
                and build_params["SCENARIO"] == scenario
                and build_params["PLATFORM"] == platform
                and build_params["ANSIBLE_VERSION"] == ansible_version
                and build_params["BUNDLE"] == 'no'
                and current_release_pipeline_id == release_pipeline_build_id
            ):
                return builds[build_id]


def get_package_based_job_results(builds, tower_version, release_pipeline_build_id):
    PARAMS_SET = [
        {
            "tower_version": tower_version,
            "ansible_version": "stable-2.9",
            "scenario": "standalone",
            "platform": "rhel-8.1-x86_64",
            "release_pipeline_build_id": release_pipeline_build_id,
        },
        {
            "tower_version": tower_version,
            "ansible_version": "stable-2.9",
            "scenario": "cluster",
            "platform": "rhel-8.1-x86_64",
            "release_pipeline_build_id": release_pipeline_build_id,
        },
        {
            "tower_version": tower_version,
            "ansible_version": "stable-2.9",
            "scenario": "standalone",
            "platform": "rhel-7.7-x86_64",
            "release_pipeline_build_id": release_pipeline_build_id,
        },
        {
            "tower_version": tower_version,
            "ansible_version": "stable-2.9",
            "scenario": "cluster",
            "platform": "rhel-7.7-x86_64",
            "release_pipeline_build_id": release_pipeline_build_id,
        },
    ]
    results = []

    for params in PARAMS_SET:
        build = did_it_run(builds, **params)
        results.append(generate_message(build, **params))

    return results


def get_openshift_based_job_results(builds, tower_version, release_pipeline_build_id):

    params = {
        "tower_version": tower_version,
        "scenario": "openshift",
        "release_pipeline_build_id": release_pipeline_build_id,
    }

    build = did_it_run(builds, **params)

    return generate_message(build, **params)


def main():
    jenkins_instance = get_jenkins_instance()

    release_pipeline_build_id = int(os.getenv("RELEASE_PIPELINE_BUILD_ID"))
    tower_version = get_tower_version_that_is_being_tested(
        jenkins_instance["Pipelines/redhat-pipeline"], release_pipeline_build_id
    )
    results = get_package_based_job_results(
        jenkins_instance["Pipelines/integration-pipeline"],
        tower_version,
        release_pipeline_build_id,
    )
    results.append(
        get_openshift_based_job_results(
            jenkins_instance["Pipelines/openshift-integration-pipeline"],
            tower_version,
            release_pipeline_build_id,
        )
    )

    print("\n".join(results))


if __name__ == "__main__":
    main()
