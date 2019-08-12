pipeline {

    agent { label 'jenkins-jnlp-agent' }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30'))
        timeout(time: 18, unit: 'HOURS')
    }

    parameters {
        string defaultValue: 'smoke.js', description: 'Specify the --filter flag for UI E2E tests if necessary', name: 'E2E_TESTEXPR'
    }

    stages {
        stage('Run yolo x10') {
            parallel {
                stage('yolo01') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo02') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo03') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo04') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo05') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo06') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo07') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo08') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo09') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
                stage('yolo10') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: 'devel'), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder')]
                    }
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts/*'
        }
    }
}