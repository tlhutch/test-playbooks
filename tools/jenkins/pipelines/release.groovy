pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.5.x', '3.4.x', '3.3.x']
        )
        choice(
            name: 'SCOPE',
            description: 'What is the scope of the verification? (Full will run all supported permutation, latest only on latest OSes)',
            choices: ['latest', 'full']
        )
    }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage ('Build Information') {
            steps {
                echo """Tower version under test: ${params.TOWER_VERSION}
Scope selected: ${params.SCOPE}"""

                script {
                    if (params.TOWER_VERSION == '3.5.x' ) {
                        _TOWER_VERSION = '3.5.1'
                    } else if (params.TOWER_VERSION == '3.4.x') {
                        _TOWER_VERSION = '3.4.4'
                    } else if (params.TOWER_VERSION == '3.3.x') {
                        _TOWER_VERSION = '3.3.6'
                    } else {
                        _TOWER_VERSION = 'devel'
                    }

                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${_TOWER_VERSION}"
                    }
                }
            }
        }

        stage('Build Tower TAR') {
            steps {
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
                    when {
                        expression {
                            return _TOWER_VERSION ==~ /3.[3-5].[0-9]*/
                        }
                    }

                    steps {
                        build(
                            job: 'debian-pipeline',
                            parameters: [
                                string(name: 'TOWER_VERSION', value: _TOWER_VERSION),
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
                                string(name: 'TOWER_VERSION', value: _TOWER_VERSION),
                                string(name: 'SCOPE', value: params.SCOPE),
                            ]
                        )
                    }
                }
            }
        }
    }
}
