pipeline {

    agent none

    parameters {
        choice(
            name: 'UPGRADE_TO',
            description: 'Tower version to upgrade to',
            choices: ['devel', '3.6.0', '3.5.4']
        )
    }

    options {
        timestamps()
        timeout(time: 10, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '10'))
    }

    stages {
        stage('Display Information') {
            steps {
                echo "Testing Upgrade to: ${params.UPGRADE_TO}"

                script {
                    if (params.UPGRADE_TO == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.UPGRADE_TO}"
                    }
                }
            }
        }

        stage('From 3.5.0') {
            steps {
                build(
                    job: 'Pipelines/openshift-upgrade-pipeline',
                    parameters: [
                        string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.0'),
                        string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO)
                    ]
                )
            }
        }

        stage('From 3.5.1') {
            steps {
                build(
                    job: 'Pipelines/openshift-upgrade-pipeline',
                    parameters: [
                        string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.1'),
                        string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO)
                    ]
                )
            }
        }

        stage('From 3.5.2') {
            steps {
                build(
                    job: 'Pipelines/openshift-upgrade-pipeline',
                    parameters: [
                        string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.2'),
                        string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO)
                    ]
                )
            }
        }

        stage('From 3.5.3') {
            steps {
                build(
                    job: 'Pipelines/openshift-upgrade-pipeline',
                    parameters: [
                        string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.3'),
                        string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO)
                    ]
                )
            }
        }

    }
}
