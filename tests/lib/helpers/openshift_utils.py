import subprocess

from openshift.helper.openshift import OpenShiftObjectHelper
from towerkit.config import config


def prep_environment():
    ret = subprocess.call('oc login -u {0} -p {1} {2} --insecure-skip-tls-verify={3}'.format(
        config.credentials.openshift.username,
        config.credentials.openshift.password,
        config.credentials.openshift.url,
        config.credentials.openshift.use_tls), shell=True)
    assert ret == 0

    ret = subprocess.call('oc project tower-qe', shell=True)
    assert ret == 0


def get_pods():
    client = OpenShiftObjectHelper(api_version='v1', kind='pod_list')
    ret = client.get_object(namespace='tower-qe')
    return [i.metadata.name for i in ret.items]


def get_tower_pods():
    pods = get_pods()
    return [pod for pod in pods if 'tower' in pod]


def scale_dc(dc, replicas):
    cmd = 'oc scale dc {0} --replicas={1}'.format(dc, str(replicas))
    ret = subprocess.call(cmd, shell=True)
    assert ret == 0


def delete_pod(pod):
    cmd = 'oc delete pod {0}'.format(pod)
    ret = subprocess.call(cmd, shell=True)
    assert ret == 0
