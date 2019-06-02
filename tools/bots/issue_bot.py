#!/usr/bin/env python

import os
import requests

from slacker import Slacker


github_token = os.getenv('GITHUB_TOKEN')
tower_version = os.getenv('TOWER_VERSION')

slack_token = os.getenv('SLACK_TOKEN')
slack_channel = os.getenv('SLACK_CHANNEL')
slack = Slacker(slack_token)

API_GITHUB = 'https://api.github.com'


def github_request(url):
    """Generic Github request handler."""

    res = requests.get(
        url,
        headers={
            'Authorization': 'token %s' % github_token,
            'Accept': 'application/vnd.github.inertia-preview+json'
        }
    )

    return res


def get_project_id_and_number(version):
    """Return the project id associated with a Tower version."""

    url = '{}/orgs/ansible/projects'.format(API_GITHUB)
    projects = github_request(url).json()

    return [(project['id'], project['number']) for project in projects if project['name'] == 'Ansible Tower {}'.format(version)][0]


def get_issues_from_project(project_id):
    """Return all the issues in a project."""

    _issues = []
    # Retrieve list of cards_url
    url = '{}/projects/{}/columns'.format(API_GITHUB, project_id)

    _columns = github_request(url).json()
    cards_url = [column['cards_url'] for column in _columns if 'QE' not in column['name']]

    for url in cards_url:
        _issues += [github_request(_issue['content_url']).json() for _issue in github_request(url).json()]

    return [issue for issue in _issues if issue['state'] == 'open']


def is_issue_in_need_test(issue):

    for label in issue['labels']:
        if label['name'] == 'state:needs_test':
            return True

    return False


def post_slack_msg(text):
    slack.chat.post_message(slack_channel, text, icon_emoji=':ansible:')


def create_issue_update():

    project_id, project_number = get_project_id_and_number(tower_version)
    issues = get_issues_from_project(project_id)

    needs_test = 0
    for issue in issues:
        if is_issue_in_need_test(issue):
            needs_test += 1

    url = 'https://github.com/issues?q=is:open+is:issue+project:ansible/{}'.format(
        project_number
    )
    return "{} open issues in project `{}` ({} in `state:needs_test`) - Link: {}".format(
        len(issues), tower_version, needs_test, url
    )


post_slack_msg(create_issue_update())

if __name__ == '__main__':
    create_issue_update()
