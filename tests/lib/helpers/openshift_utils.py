import os
import subprocess
import yaml

from openshift.helper.openshift import OpenShiftObjectHelper
from awxkit.config import config


def get_openshift_credentials():
    creds = {'username': '', 'password': '', 'host': '', 'project': '', 'token': ''}
    installer_vars = None
    vars_path = 'artifacts/openshift_installer_vars.yml'
    if os.path.exists(vars_path):
        with open(vars_path) as f:
            installer_vars = yaml.safe_load(f)
        creds['username'] = installer_vars.get('openshift_user')
        creds['host'] = installer_vars.get('openshift_host')
        creds['project'] = installer_vars.get('openshift_project')
        creds['token'] = installer_vars.get('openshift_token')
        creds['password'] = installer_vars.get('openshift_password')

    # Always override with environment variables if possible
    creds['username'] = os.getenv('OPENSHIFT_USER') if os.getenv('OPENSHIFT_USER', False) else creds['username']
    creds['token'] = os.getenv('OPENSHIFT_TOKEN') if os.getenv('OPENSHIFT_TOKEN', False) else creds['token']
    creds['password'] = os.getenv('OPENSHIFT_PASSWORD') if os.getenv('OPENSHIFT_PASSWORD', False) else creds['password']
    creds['host'] = os.getenv('OPENSHIFT_HOST') if os.getenv('OPENSHIFT_HOST', False) else creds['host']
    creds['project'] = os.getenv('OPENSHIFT_PROJECT') if os.getenv('OPENSHIFT_PROJECT', False) else creds['project']

    # Only if nothing else has been provided use credentials file
    if not creds['username']:
        creds['username'] = config.credentials.openshift.username
    # Only use password if token and pasword is not set from other source
    if not creds['token'] and not creds['password']:
        creds['password'] = config.credentials.openshift.password
    if not creds['host']:
        creds['host'] = config.credentials.openshift.host
    if not creds['project']:
        creds['project'] = config.credentials.openshift.project

    return creds


def prep_environment():
    creds = get_openshift_credentials()
    if creds['token']:
        ret = subprocess.call('oc login --token {0} {1} --insecure-skip-tls-verify'.format(
            creds['token'],
            creds['host']), shell=True)
    else:
        ret = subprocess.call('oc login -u {0} -p {1} {2} --insecure-skip-tls-verify'.format(
            creds['username'],
            creds['password'],
            creds['host']), shell=True)
    assert ret == 0

    ret = subprocess.call('oc project {}'.format(creds['project']), shell=True)
    assert ret == 0


def get_pods():
    namespace = get_openshift_credentials()['project']
    client = OpenShiftObjectHelper(api_version='v1', kind='pod_list')
    ret = client.get_object(namespace=namespace)
    return [i.metadata.name for i in ret.items]


def get_tower_pods():
    pods = get_pods()
    return [pod for pod in pods if 'ansible-tower' in pod]


def scale_dc(dc, replicas):
    cmd = 'oc scale sts {0} --replicas={1}'.format(dc, str(replicas))
    ret = subprocess.call(cmd, shell=True)
    assert ret == 0


def delete_pod(pod):
    cmd = 'oc delete pod {0}'.format(pod)
    ret = subprocess.call(cmd, shell=True)
    assert ret == 0
