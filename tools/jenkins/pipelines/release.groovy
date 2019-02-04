pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.4.2', '3.3.5', '3.2.9']
        )
    }

    stages {

        stage ('Build Information') {
            steps {
                echo "Tower version under test: ${params.TOWER_VERSION}"
            }
        }

        stage('Build Tower TAR') {
            steps {
                script {
                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.TOWER_VERSION}"
                    }
                }
                build(
                    job: 'Build_Tower_TAR',
                    parameters: [
                       string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                    ]
                )
            }
        }

        stage('OS Variant') {
            parallel {
                stage('Debian') {
                    steps {
                        build(
                            job: 'debian-pipeline',
                            parameters: [
                                string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                            ]
                        )
                    }
                }
                stage('Red Hat') {
                    steps {
                        build(
                            job: 'redhat-pipeline',
                            parameters: [
                                string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                            ]
                        )
                    }
                }
            }
        }
    }
}
