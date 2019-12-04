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
            name: 'E2E_SCRIPT_BRANCH',
            description: 'This is actually a branch of tower-qa repository, but only for choosing a version of e2e.sh to run. Assumes the ansible fork of tower-qa.',
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
        booleanParam(
            name: 'E2E_RUN_EXTERNAL_GRID',
            description: 'Run tests on an External Selenium Grid', 
            defaultValue: 'false'
        )
        string(
            name: 'E2E_EXTERNAL_GRID_HOSTNAME',
            description: 'External Selenium Grid option', 
            defaultValue: 'hub'
        )
        string(
            name: 'E2E_EXTERNAL_GRID_PORT',
            description: 'External Selenium Grid option', 
            defaultValue: '4444'
        )
    }
    options {
        timeout(time: 2, unit: 'HOURS')
        timestamps()
        ansiColor('xterm')
        buildDiscarder(logRotator(daysToKeepStr: '10'))
    }
    stages {
        stage ('Clone Git repo') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [
                        [ name: '*/${E2E_SCRIPT_BRANCH}' ]
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
                            credentialsId: 'github-ansible-jenkins-nopassphrase',
                            url: 'git@github.com:ansible/tower-qa.git'
                        ]
                    ]
                ])
            }
        }
        stage('Call e2e.sh') {
            steps{
                script {
                    if  (params.E2E_RUN_EXTERNAL_GRID) {
                        env.E2E_EXTERNAL_GRID_HOSTNAME = "zalenium-zalenium2.cloud.paas.psi.redhat.com"
                        env.E2E_EXTERNAL_GRID_PORT = "80"
                    }  
                }
                withCredentials([file(credentialsId: '86ed99e9-dad9-49e9-b0db-9257fb563bad', variable: 'JSON_KEY_FILE_PATH')]) {
                    sshagent(['github-ansible-jenkins-nopassphrase']) {
                        sh '''#!/bin/bash
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
                            E2E_EXTERNAL_GRID_HOSTNAME=${E2E_EXTERNAL_GRID_HOSTNAME} \
                            E2E_EXTERNAL_GRID_PORT=${E2E_EXTERNAL_GRID_PORT} \
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
                  thresholds: [failed(failureThreshold: '50', unstableThreshold: '1'), skipped(failureThreshold: '50', unstableThreshold: '1')], 
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

