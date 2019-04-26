pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.5.0', '3.4.4', '3.3.6']
        )
        choice(
            name: 'SCOPE',
            description: 'What is the scope of the verification? (Full will run all supported permutation, latest only on latest OSes)',
            choices: ['latest', 'full']
        )
        choice(
            name: 'RUN_UPGRADE',
            description: 'Should the upgrade jobs be run ?',
            choices: ['yes', 'no']
        )
        choice(
            name: 'RUN_BACKUP_AND_RESTORE',
            description: 'Should the backup and restore jobs be run ?',
            choices: ['yes', 'no']
        )
        choice(
            name: 'RUN_INTEGRATION',
            description: 'Should the integration jobs be run ?',
            choices: ['yes', 'no']
        )
    }

    stages {

        stage('Build DEB') {
            steps {
                script {
                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.TOWER_VERSION}"
                    }
                }
                build(
                    job: 'Build_Tower_DEB',
                    parameters: [
                       string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                       string(name: 'DEB_DIST', value: '"xenial"'),
                       booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
                script {
                    if (params.TOWER_VERSION == '3.3.5') {
                        build(
                            job: 'Build_Tower_DEB',
                            parameters: [
                                string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                                string(name: 'DEB_DIST', value: '"trusty"'),
                                booleanParam(name: 'TRIGGER', value: false)
                            ]
                        )
                    }
                }
            }
        }

        stage('Operating System') {
            steps {
                script {
                    def tasks = [:]
                    def oses = [:]


                    if (params.SCOPE == 'latest' || params.TOWER_VERSION !=~ /3\.[0-3]*\.[0-9]*/) {
                        oses = ['ubuntu-16.04-x86_64']
                    } else {
                        oses = ['ubuntu-14.04-x86_64', 'ubuntu-16.04-x86_64']
                    }

                    for (int i=0;i<oses.size(); i++) {
                         def os = oses[i]

                         tasks[os] = {
                            build(
                                job: 'dispatch-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                    string(name: 'PLATFORM', value: os),
                                    string(name: 'RUN_UPGRADE', value: params.RUN_UPGRADE),
                                    string(name: 'RUN_BACKUP_AND_RESTORE', value: params.RUN_BACKUP_AND_RESTORE),
                                    string(name: 'RUN_INTEGRATION', value: params.RUN_INTEGRATION),
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
