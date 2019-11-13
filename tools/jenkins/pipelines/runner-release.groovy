pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        string(
            name: 'RUNNER_FORK',
            description: 'Fork of ansible-runner to deploy.',
            defaultValue: 'ansible'
        )
        string(
            name: 'RUNNER_BRANCH',
            description: 'Branch to use for ansible-runner.',
            defaultValue: 'master'
        )
    }

    options {
        timestamps()
        timeout(time: 12, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }


    stages {

        stage('Trigger Slowyos') {
            parallel {
                stage('EL7/Standalone') {
                    steps {
                        build(
                            job: 'Test_Tower_Yolo_Express',
                            parameters: [
                                string(name: 'PLATFORM', value: 'rhel-7.6-x86_64'),
                                string(name: 'PRODUCT', value: 'tower'),
                                string(name: 'COMMENTS', value: "ansible/ansible-runner el7/standalone"),
                                string(name: 'RUNNER_FORK', value: params.RUNNER_FORK),
                                string(name: 'RUNNER_BRANCH', value: params.RUNNER_BRANCH),
                                string(name: 'TESTEXPR', value: 'test'),
                                string(name: 'ANSIBLE_NIGHTLY_BRANCH', value: 'stable-2.9'),
                                booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: false),
                                booleanParam(name: 'RUN_E2E', value: false),
                                booleanParam(name: 'RUN_CLI_TESTS', value: false)
                            ]
                        )
                    }
                }
                stage('EL7/Cluster') {
                    steps {
                        build(
                            job: 'Test_Tower_Yolo_Express',
                            parameters: [
                                string(name: 'PLATFORM', value: 'rhel-7.6-x86_64'),
                                string(name: 'PRODUCT', value: 'tower'),
                                string(name: 'SCENARIO', value: 'cluster'),
                                string(name: 'COMMENTS', value: "ansible/ansible-runner el7/cluster"),
                                string(name: 'RUNNER_FORK', value: params.RUNNER_FORK),
                                string(name: 'RUNNER_BRANCH', value: params.RUNNER_BRANCH),
                                string(name: 'TESTEXPR', value: 'test'),
                                string(name: 'ANSIBLE_NIGHTLY_BRANCH', value: 'stable-2.9'),
                                booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: false),
                                booleanParam(name: 'RUN_E2E', value: false),
                                booleanParam(name: 'RUN_CLI_TESTS', value: false)
                            ]
                        )
                    }
                }
                stage('EL8/Standalone') {
                    steps {
                        build(
                            job: 'Test_Tower_Yolo_Express',
                            parameters: [
                                string(name: 'PLATFORM', value: 'rhel-8.1-x86_64'),
                                string(name: 'PRODUCT', value: 'tower'),
                                string(name: 'COMMENTS', value: "ansible/ansible-runner el8/standalone"),
                                string(name: 'RUNNER_FORK', value: params.RUNNER_FORK),
                                string(name: 'RUNNER_BRANCH', value: params.RUNNER_BRANCH),
                                string(name: 'TESTEXPR', value: 'test'),
                                string(name: 'ANSIBLE_NIGHTLY_BRANCH', value: 'stable-2.9'),
                                booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: false),
                                booleanParam(name: 'RUN_E2E', value: false),
                                booleanParam(name: 'RUN_CLI_TESTS', value: false)
                            ]
                        )
                    }
                }
                stage('EL8/Cluster') {
                    steps {
                        build(
                            job: 'Test_Tower_Yolo_Express',
                            parameters: [
                                string(name: 'PLATFORM', value: 'rhel-8.1-x86_64'),
                                string(name: 'PRODUCT', value: 'tower'),
                                string(name: 'SCENARIO', value: 'cluster'),
                                string(name: 'COMMENTS', value: "ansible/ansible-runner el8/cluster"),
                                string(name: 'RUNNER_FORK', value: params.RUNNER_FORK),
                                string(name: 'RUNNER_BRANCH', value: params.RUNNER_BRANCH),
                                string(name: 'TESTEXPR', value: 'test'),
                                string(name: 'ANSIBLE_NIGHTLY_BRANCH', value: 'stable-2.9'),
                                booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: false),
                                booleanParam(name: 'RUN_E2E', value: false),
                                booleanParam(name: 'RUN_CLI_TESTS', value: false)
                            ]
                        )
                    }
                }
            }
        }
    }
}

