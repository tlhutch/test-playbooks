#!/usr/bin/env python3

import subprocess
import json

p = subprocess.run("docker ps | egrep -o 'tools_awx(_run)?_([^ ]+)?'", stdout=subprocess.PIPE, shell=True)
docker_host = p.stdout.decode('utf-8').rstrip()

out = {
    'local': {
        'hosts': ['127.0.0.1'],
        'vars': {
            'ansible_connection': 'local',
            'ansible_python_interpreter': '/usr/bin/env python',
        },
    },
    'tower': {
        'hosts': [docker_host],
        'vars': {
            'ansible_connection': 'docker',
            'ansible_user': 'awx'
        }
    },
    "_meta": {
        "hostvars": {
            "127.0.0.1": {
                'ansible_connection': 'local',
                'ansible_python_interpreter': '/usr/bin/env python',
            },
            docker_host: {
                'ansible_connection': 'docker',
                'ansible_user': 'awx'
            }
        }
    }
}
print(json.dumps(out))

