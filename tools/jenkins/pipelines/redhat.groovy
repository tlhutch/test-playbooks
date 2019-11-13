pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.6.1', '3.5.4', '3.4.6', '3.3.8']
        )
        choice(
            name: 'SCOPE',
            description: 'What is the scope of the verification? (Full will run all supported permutation, latest only on latest OSes)',
            choices: ['latest', 'full']
        )
    }

    options {
        timestamps()
        timeout(time: 18, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage('Build Information') {
            steps {
                echo """Tower version under test: ${params.TOWER_VERSION}
Scope selected: ${params.SCOPE}"""

                script {
                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.TOWER_VERSION}"
                    }
                }
            }
        }

        stage('Build RPM and Artifacts') {
            parallel {
                stage('epel-7-rpm') {
                    steps {
                        build(
                            job: 'Build_Tower_RPM',
                            parameters: [
                               string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                               booleanParam(name: 'TRIGGER', value: false),
                               string(name: 'TARGET_DIST', value: 'epel-7-x86_64'),
                               string(name: 'MOCK_CFG', value: 'rhel-7-x86_64')
                            ]
                        )
                    }
                }
                stage('epel-8-rpm') {
                    when {
                        expression {
                            return !(params.TOWER_VERSION ==~ /3.[3-4].[0-9]*/)
                        }
                    }

                    steps {
                        build(
                            job: 'Build_Tower_RPM',
                            parameters: [
                               string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                               booleanParam(name: 'TRIGGER', value: false),
                               string(name: 'TARGET_DIST', value: 'epel-8-x86_64'),
                               string(name: 'MOCK_CFG', value: 'rhel-8-x86_64')
                            ]
                        )
                    }
                }

                stage('build-awx-cli') {
                    when {
                        expression {
                            return !(params.TOWER_VERSION ==~ /3.[3-5].[0-9]*/)
                        }
                    }

                    steps {
                        build(
                            job: 'Build_AWX_CLI',
                            parameters: [
                              string(name: 'TOWER_PACKAGING_BRANCH', value: branch_name),
                            ]
                        )
                    }
                }
            }
        }

        stage('Build Bundle and Generate CLI doc') {
            parallel {
                stage('epel-7-bundle') {
                    steps {
                        build(
                            job: 'Build_Tower_Bundle_TAR',
                            parameters: [
                               string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                               string(name: 'TARGET_DIST', value: 'epel-7-x86_64'),
                               booleanParam(name: 'TRIGGER', value: false)
                            ]
                        )
                    }
                }
                stage('epel-8-bundle') {
                    when {
                        expression {
                            return !(params.TOWER_VERSION ==~ /3.[3-4].[0-9]*/)
                        }
                    }

                    steps {
                        build(
                            job: 'Build_Tower_Bundle_TAR',
                            parameters: [
                               string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                               string(name: 'TARGET_DIST', value: 'epel-8-x86_64'),
                               booleanParam(name: 'TRIGGER', value: false)
                            ]
                        )
                    }
                }
                stage('generate-cli-doc') {
                    when {
                        expression {
                            return !(params.TOWER_VERSION ==~ /3.[3-5].[0-9]*/)
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'build-awx-cli-docs',
                                parameters: [
                                   string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('Operating System') {
            steps {
                script {
                    def tasks = [:]
                    def oses = ['rhel-7.4-x86_64', 'rhel-7.5-x86_64', 'rhel-7.6-x86_64', 'rhel-7.7-x86_64', 'rhel-8.0-x86_64', 'rhel-8.1-x86_64', 'centos-7.latest-x86_64']

                    if (params.SCOPE == 'latest' && params.TOWER_VERSION ==~ /3.[3-4].[0-9]*/) {
                        oses = ['rhel-7.7-x86_64']
                    } else if (params.SCOPE == 'latest') {
                        oses = ['rhel-7.7-x86_64', 'rhel-8.1-x86_64']
                    } else {
                        oses = ['rhel-7.4-x86_64', 'rhel-7.5-x86_64', 'rhel-7.6-x86_64', 'rhel-7.7-x86_64', 'rhel-8.0-x86_64', 'rhel-8.1-x86_64', 'centos-7.latest-x86_64']
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
