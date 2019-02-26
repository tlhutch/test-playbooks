pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.4.2', '3.3.5', '3.2.9']
        )
        choice(
            name: 'SCOPE',
            description: 'What is the scope of the verification? (Full will run all supported permutation, latest only on latest OSes)',
            choices: ['latest', 'full']
        )
    }

    stages {

        stage('Build RPM') {
            steps {
                script {
                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.TOWER_VERSION}"
                    }
                }
                build(
                    job: 'Build_Tower_RPM',
                    parameters: [
                       string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                       booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('Build Bundle TAR') {
            steps {
                build(
                    job: 'Build_Tower_Bundle_TAR',
                    parameters: [
                       string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                       booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('Operating System') {
            steps {
                script {
                    def tasks = [:]
                    def oses = ['rhel-7.4-x86_64', 'rhel-7.5-x86_64', 'rhel-7.6-x86_64', 'centos-7.latest-x86_64', 'ol-7.6-x86_64']

                    if (params.SCOPE == 'latest') {
                        oses = ['rhel-7.6-x86_64']
                    } else {
                        oses = ['rhel-7.4-x86_64', 'rhel-7.5-x86_64', 'rhel-7.6-x86_64', 'centos-7.latest-x86_64', 'ol-7.6-x86_64']
                    }

                    for (int i=0;i<oses.size(); i++) {
                         def os = oses[i]

                         tasks[os] = {
                            build(
                                job: 'dispatch-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                    string(name: 'PLATFORM', value: os)
                                ]
                            )
                         }
                    }

                    stage('Operating System') {
                        parallel tasks
                    }
                }
            }
        }
    }
}
