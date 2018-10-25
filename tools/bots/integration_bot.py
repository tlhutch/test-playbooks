#!/usr/bin/env python

from collections import namedtuple
from datetime import datetime, timedelta
import os
import pytz
import re

from jenkinsapi.jenkins import Jenkins
from slacker import Slacker


jenkins_url = os.getenv('JENKINS_URL')
jenkins_username = os.getenv('JENKINS_USERNAME')
jenkins_token = os.getenv('JENKINS_TOKEN')
server = Jenkins(jenkins_url, username=jenkins_username, password=jenkins_token)

slack_token = os.getenv('SLACK_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL')
slack = Slacker(slack_token)

job_name = os.getenv('JOB_NAME')
matrix_job = os.getenv('MATRIX_JOB', 'False')
build_label = os.getenv('BUILD_LABEL')

show_button_owner = os.getenv('SHOW_BUTTON_OWNER')


def get_test_results():
    """
    Returns either:
    - (<number of currently failing tests>, <url of most recent nightly test run>, <change in test failures>, <url of prior nightly test run>)
    - (-1, None, 0, None) if last test run did not occur in past 24 hours, or
    - (-2, None, 0, None) if test results were not found
    """
    buildresult = namedtuple('buildresult', 'failures, url')

    def result_from_past_day(build):
        timestamp = build.get_timestamp()
        today = datetime.now(pytz.UTC)
        if today - timestamp > timedelta(days=1):
            return False
        return True

    job = server.get_job(job_name)
    build_ids = sorted([id for id in job.get_build_ids()], reverse=True)

    failure_history = []
    found_first_result = False
    for id in build_ids:
        build = job.get_build(id)
        output = build.get_console()
        if 'Started by timer' not in output:
            user = re.search(r'Started by user ([\w ]+)', output).group(1)
            print 'Skipping {} (manually launched by {})'.format(build.name, user)
            continue
        runs = []
        if matrix_job.lower() == 'true':
            runs = build.get_matrix_runs()
        else:
            runs = [build]

        for run in runs:
            url = run.baseurl
            desc = run.get_description()
            if not desc:
                continue
            if matrix_job.lower() == 'true' and build_label not in desc:
                continue

            desc = desc.lower()
            results = {'passed': 0, 'failed': 0, 'error': 0}
            for result in results:
                res = re.search(r'(\d+) {}'.format(result), desc)
                if not res:
                    continue
                results[result] = int(res.group(1))
            if not any(results.values()):
                continue

            if results['passed']:
                if not found_first_result:
                    if result_from_past_day(run):
                        return (0, None, 0, None)
                    return (-1, None, 0, None)
                else:
                    # Test was passing, now failing
                    return (
                        failure_history[0].failures,
                        failure_history[0].url,
                        failure_history[1].failures,
                        failure_history[1].url
                    )

            total_failures = results['failed'] + results['error']
            failure_history.append(buildresult(total_failures, url))
            if not found_first_result and len(failure_history) == 1:
                found_first_result = True
                if not result_from_past_day(build):
                    return (-1, None, None, None)

            if len(failure_history) == 2:
                return (
                    failure_history[0].failures,
                    failure_history[0].url,
                    failure_history[0].failures - failure_history[1].failures,
                    failure_history[1].url
                )

    return (-2, None, 0, None)


def post_slack_msg(text):
    slack.chat.post_message(slack_channel, text, icon_emoji=':ansible:')


def create_test_update():
    total_failures, url, change, old_url = get_test_results()

    if total_failures == 0:
        post_slack_msg(':green_ball: *{0}* ({1}) is green! :green_ball:'.format(job_name, url))
        return

    if total_failures == -1:
        post_slack_msg(':skull_and_crossbones: *{0}* failed to run :skull_and_crossbones:'.format(job_name))
        return
    if total_failures == -2:
        post_slack_msg(':construction: Failed to find results for *{0}* :construction:'.format(job_name))
        return

    emoji_map = {20: ':tornado:',
                 15: ':thunder_cloud_and_rain:',
                 10: ':rain_cloud:',
                 5: ':cloud:',
                 0: ':barely_sunny:',
                 -5: ':mostly_sunny:',
                 -10: ':sunrise_over_mountains:',
                 -15: ':sunrise:'}
    emoji = ':tornado:'
    for level in sorted(emoji_map.keys()):
        if change <= level:
            emoji = emoji_map[level]
            break

    if change > 0:
        description = '*{0}* ({1}) has {2} more failures than {3}'.format(job_name, url, change, old_url)
    elif change == 0:
        description = '*{0}* ({1}) has the same number of failures as {3}'.format(job_name, url, old_url)
    else:
        change = -change
        description = '*{0}* ({1}) has {2} fewer failures than {3}'.format(job_name, url, change, old_url)

    day_of_the_week = datetime.today().weekday()
    button_owner_map = {0: 'spredzy',
                        1: 'one-t',
                        2: 'elijahd',
                        3: 'jladd',
                        4: 'elyezer'}

    button_owner_msg = ''
    if show_button_owner.lower() == 'true' and day_of_the_week < 5:
        button_owner_msg = '\nButton: {0}'.format(button_owner_map[day_of_the_week])

    post_slack_msg('{0} {1}\nTotal failures: {2}{3}'.format(description, emoji, total_failures, button_owner_msg))


if __name__ == '__main__':
    create_test_update()
