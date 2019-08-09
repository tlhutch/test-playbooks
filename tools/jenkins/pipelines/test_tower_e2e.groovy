pipeline {
    agent {
        label 'jenkins-jnlp-agent'
    }
    parameters {
        string(
            name: 'E2E_URL',
            description: 'E2E test target URL. Include https:// as applicable.',
        )
        string(
            name: 'DEPLOYMENT_TYPE',
            description: 'awx or tower',
            defaultValue: 'awx'
        )
        string(
            name: 'E2E_FORK',
            description: 'Fork of E2E test repository.',
            defaultValue: 'ansible'
        )
        string(
            name: 'E2E_BRANCH',
            description: 'Branch of E2E test repository.',
            defaultValue: 'devel'
        )
        string(
            name: 'TOWER_QA_BRANCH',
            description: 'Branch of tower-qa repository. This is for choosing a version of e2e.sh to run.',
            defaultValue: 'devel'
        )
        string(
            name: 'SELENIUM_DOCKER_TAG',
            description: 'Docker tag for selenium/node-chrome and selenium/node-firefox. Only change this if there is an unstable docker release.',
            defaultValue: 'latest'
        )
        string(
            name: 'E2E_USERNAME',
            description: 'Username used during E2E tests.',
            defaultValue: 'admin'
        )
        password(
            name: 'E2E_PASSWORD',
            description: 'Password used during E2E tests.',
        )
        string(
            name: 'E2E_TEST_SELECTION',
            description: 'Value of the nightwatchJS --filter option.',
            defaultValue: '*'
        )
        string(
            name: 'E2E_RETRIES',
            description: 'Retry testsuites multiple times.', 
            defaultValue: '2'
        )
    }
    options {
        timeout(time: 2, unit: 'HOURS')
        timestamps()
        ansiColor('xterm')
    }
    stages {
        stage ('Clone Git repo') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [
                        [ name: '*/${TOWER_QA_BRANCH}' ]
                    ],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [
                        [
                            $class: 'CloneOption', 
                            noTags: false, 
                            reference: '', 
                            shallow: true
                        ]
                    ],
                    submoduleCfg: [],
                    userRemoteConfigs: [
                        [
                            credentialsId: '55b638c7-3ef3-4679-9020-fa09e411a74d',
                            url: 'https://github.com/ansible/tower-qa'
                        ]
                    ]
                ])
            }
        }
        stage('Call e2e.sh') {
            steps{
                withCredentials([string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD'),
                                file(credentialsId: '86ed99e9-dad9-49e9-b0db-9257fb563bad', variable: 'JSON_KEY_FILE_PATH')]) {
                    sshagent(['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                        sh '''#!/bin/bash
                        AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD} \
                            E2E_URL=${E2E_URL} \
                            DEPLOYMENT_TYPE=${DEPLOYMENT_TYPE} \
                            E2E_FORK=${E2E_FORK} \
                            E2E_BRANCH=${E2E_BRANCH} \
                            E2E_RETRIES=${E2E_RETRIES} \
                            SELENIUM_DOCKER_TAG=${SELENIUM_DOCKER_TAG} \
                            E2E_USERNAME=${E2E_USERNAME} \
                            E2E_PASSWORD=${E2E_PASSWORD} \
                            E2E_TEST_SELECTION=${E2E_TEST_SELECTION} \
                            JSON_KEY_FILE_PATH=${JSON_KEY_FILE_PATH} \
                            ./tools/jenkins/scripts/e2e.sh
                        '''
                    }
                }
            }
        }
    }
    post {
        always {
            xunit reduceLog: false, 
                  testTimeMargin: '15000',
                  thresholds: [failed(failureThreshold: '1'), skipped(failureThreshold: '1')], 
                  tools: [
                      Custom(customXSL: '${DEPLOYMENT_TYPE}/awx/ui/test/e2e/nightwatchxsl.xsl', 
                          deleteOutputFiles: false, 
                          failIfNotNew: false, 
                          pattern: '${DEPLOYMENT_TYPE}/awx/ui/test/e2e/reports/*.xml', 
                          skipNoTestFiles: false, 
                          stopProcessingIfError: true)]
            archiveArtifacts '${DEPLOYMENT_TYPE}/awx/ui/test/e2e/reports/*.xml,${DEPLOYMENT_TYPE}/awx/ui/test/e2e/screenshots/**'
        }
    }
}

