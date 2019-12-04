pipeline {

    agent { label 'jenkins-jnlp-agent' }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '10'))
        timeout(time: 18, unit: 'HOURS')
    }

    parameters {
        string name: 'E2E_TESTEXPR', defaultValue: '*', description: 'Specify the --filter flag for UI E2E tests if necessary'
        string(
            name: 'SLACK_USERNAME',
            description: """\
            Send slack DM on completion. Use space separate list to sent to multiple people, for example: @johill @elyezer.
            Will always go to #CICI
            """,
            defaultValue: '@yournamehere'
        )
        string(
            name: 'E2E_FORK', 
            defaultValue: 'ansible', 
            description: 'Git fork of E2E tests'
        )
        string(
            name: 'E2E_BRANCH',
            defaultValue: 'devel',
            description: 'Git branch of E2E tests'
        )
        booleanParam(
            name: 'E2E_RUN_EXTERNAL_GRID',
            description: 'Select to run e2e tests against an external selenium grid',
            defaultValue: false
        )
    }

    stages {
        stage('Run yolo x10') {
            parallel {
                stage('yolo01') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo02') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo03') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo04') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo05') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo06') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo07') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo08') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo09') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
                stage('yolo10') {
                    steps {
                        build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'awx'), string(name: 'TOWER_FORK', value: "${params.E2E_FORK}"), string(name: 'TOWER_BRANCH', value: "${params.E2E_BRANCH}"), string(name: 'TOWER_QA_FORK', value: 'ansible'), string(name: 'TOWER_QA_BRANCH', value: 'devel'), booleanParam(name: 'BUILD_INSTALLER_AND_PACKAGE', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), booleanParam(name: 'RETRY_FAILED_TESTS', value: false), string(name: 'TESTEXPR', value: 'yolo or ansible_integration'), string(name: 'E2E_TESTEXPR', value: "${params.E2E_TESTEXPR}"), string(name: 'SLACK_USERNAME', value: '#cici'), booleanParam(name: 'TEARDOWN_INSTANCE_ON_SUCCESS', value: true), string(name: 'COMMENTS', value: 'flakefinder'), booleanParam(name: 'E2E_RUN_EXTERNAL_GRID', value: "${params.E2E_RUN_EXTERNAL_GRID}")]
                    }
                }
            }
        }
    }
    post {
        always {
            archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts/*'
        }
        success {
            slackSend(
                botUser: false,
                color: "good",
                teamDomain: "ansible",
                channel: "#CICI ${params.SLACK_USERNAME}",
                message: "<${env.RUN_DISPLAY_URL}|flakefinder #${env.BUILD_ID}> success"
            )
        }
        failure {
            slackSend(
                botUser: false,
                color: "danger",
                teamDomain: "ansible",
                channel: "#CICI ${params.SLACK_USERNAME}",
                message: "<${env.RUN_DISPLAY_URL}|flakefinder #${env.BUILD_ID}> failure"
            )
        }
        unstable {
            slackSend(
                botUser: false,
                color: "warning",
                teamDomain: "ansible",
                channel: "#CICI ${params.SLACK_USERNAME}",
                message: "<${env.RUN_DISPLAY_URL}|flakefinder #${env.BUILD_ID}> unstable"
            )
        }
    }
}
