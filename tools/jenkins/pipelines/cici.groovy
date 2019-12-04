pipeline {
    agent {
        label 'jenkins-jnlp-agent'
    }
    environment {
        TOWER_BRANCH = 'devel'
    }
    triggers {
        cron('H */4 * * *')
    }
    options {
        disableConcurrentBuilds()
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '10'))
    }
    stages {
        stage('Checkout tower branch') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [
                        [ name: env.TOWER_BRANCH ]
                    ],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    submoduleCfg: [],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'github-ansible-jenkins-nopassphrase',
                            url: 'git@github.com:ansible/awx.git'
                        ]
                    ]
                ])
            }
        }
        stage('Run Yolo with params') {
            steps {
                build job: 'Test_Tower_Yolo_Express', parameters: [string(name: 'PRODUCT', value: 'tower'), string(name: 'TOWER_FORK', value: 'ansible'), string(name: 'TOWER_PACKAGING_FORK', value: 'ansible'), string(name: 'TOWER_BRANCH', value: "${TOWER_BRANCH}"), string(name: 'TOWER_PACKAGING_BRANCH', value: "${TOWER_BRANCH}"), string(name: 'TOWER_QA_BRANCH', value: "${TOWER_BRANCH}"), string(name: 'TOWERKIT_BRANCH', value: "${TOWER_BRANCH}"), booleanParam(name: 'BUILD_INSTALLER', value: true), booleanParam(name: 'BUILD_RPM', value: true), booleanParam(name: 'RUN_INSTALLER', value: true), booleanParam(name: 'RUN_TESTS', value: false), booleanParam(name: 'RUN_E2E', value: true), string(name: 'TESTEXPR', value: ''), string(name: 'CUSTOM_INSTANCE_PREFIX', value: 'CICI-${TOWER_BRANCH}'), string(name: 'PLATFORM', value: 'rhel-7.5-x86_64'), booleanParam(name: 'PARALLEL', value: true), string(name: 'ANSIBLE_NIGHTLY_BRANCH', value: 'stable-2.7')]
            }
        }
        stage('Copy test results') {
            steps {
                copyArtifacts filter: 'awx/ui/test/e2e/reports/*.xml', optional: true, fingerprintArtifacts: true, flatten: false, projectName: 'Test_Tower_E2E', selector: lastCompleted()
                junit allowEmptyResults: false, testResults: 'awx/ui/test/e2e/reports/*.xml'
            }
        }
    }
    post {
        always {
            logstashSend failBuild: false, maxLines: 0
            slackSend(
                color: "good",
                teamDomain: "ansible",
                channel: "#cici",
                message: "CIC ${TOWER_BRANCH} is <${env.RUN_DISPLAY_URL}|Job Dun>"
            )
        }
    }
}
