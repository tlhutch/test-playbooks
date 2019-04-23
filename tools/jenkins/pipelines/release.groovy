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
    }

    stages {

        stage ('Build Information') {
            steps {
                echo """Tower version under test: ${params.TOWER_VERSION}
Scope selected: ${params.SCOPE}"""
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
                                string(name: 'SCOPE', value: params.SCOPE),
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
                                string(name: 'SCOPE', value: params.SCOPE),
                            ]
                        )
                    }
                }
            }
        }
    }
}
