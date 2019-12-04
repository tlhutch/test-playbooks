pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to test',
            choices: ['devel', '3.6.2', '3.5.4', '3.4.6', '3.3.8']
        )
        choice(
            name: 'PLATFORM',
            description: 'The OS to install the Tower instance on',
            choices: ['rhel-7.7-x86_64', 'rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'rhel-8.1-x86_64', 'rhel-8.0-x86_64', 'centos-7.latest-x86_64',
                      'ubuntu-16.04-x86_64', 'ubuntu-14.04-x86_64']
        )
    }

    options {
        timestamps()
        timeout(time: 18, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '10'))
    }

    stages {
        stage('Ansible Versions') {
            steps {
                script {
                    def tasks = [:]
                    def ansible_versions = [:]

                    if (params.PLATFORM.contains('rhel-8')) {
                        ansible_versions = ['devel', 'stable-2.9', 'stable-2.8']
                    } else {
                        ansible_versions = ['devel', 'stable-2.9', 'stable-2.8', 'stable-2.7']
                    }

                    for(int j=0; j<ansible_versions.size(); j++) {
                        def ansible_version = ansible_versions[j]

                        tasks[ansible_version] = {
                            build(
                                job: 'verification-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                    string(name: 'ANSIBLE_VERSION', value: ansible_version),
                                    string(name: 'PLATFORM', value: params.PLATFORM)
                                ]
                            )
                        }
                    }

                    stage ('Ansible Versions') {
                        parallel tasks
                    }
                }
            }
        }
    }
}
