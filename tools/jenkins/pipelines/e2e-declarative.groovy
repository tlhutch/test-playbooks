pipeline {
    agent {
        label 'jenkins-jnlp-agent'
    }
    parameters {
        string(
            name: 'AWX_E2E_URL',
            description: 'include https://',
            defaultValue: ''
        )
        string(
            name: 'AWX_E2E_USERNAME',
            description: '',
            defaultValue: 'admin'
        )
        password(
            name: 'AWX_E2E_PASSWORD',
            description: 'Leave blank or do not edit to use default password',
        )
        string(
            name: 'TOWER_REPO',
            description: 'Point to an AWX or Tower repo',
            defaultValue: 'git@github.com:ansible/tower.git'
        )
        string(
            name: 'TOWER_BRANCH_NAME',
            description: 'Default is devel',
            defaultValue: 'origin/devel'
        )
        string(
            name: 'TEST_SELECTION',
            description: 'Run the tests selected by this pattern',
            defaultValue: '*'
        )
        booleanParam(
            name: 'ADD_LICENSE',
            description: 'Add a license to the target instance; enabled by default',
            defaultValue: true
        )
    }

    options {
        timeout(time: 2, unit: 'HOURS')
        timestamps()
        ansiColor('xterm')
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {
        stage ('Clone Git repo') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [
                        [ name: '${TOWER_BRANCH_NAME}' ]
                    ],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [],
                    submoduleCfg: [],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'd2d4d16b-dc9a-461b-bceb-601f9515c98a',
                            url: '${TOWER_REPO}'
                        ]
                    ]
                ])
            }
        }
        stage('License tower') {
            steps{
                sh '''#!/bin/bash
                        if [[ ${ADD_LICENSE} == "true" ]]; then
                        	# ensure box is licensed
                        	curl -o add_license.py https://gist.githubusercontent.com/jakemcdermott/0aac520c7bb631ee46517dfab94bd6dd/raw/fd85fdad7395f90ac4acab1b6c2edf10df0bb3d7/apply_license.py
                        	python add_license.py -u ${AWX_E2E_USERNAME} -p ${AWX_E2E_PASSWORD} ${AWX_E2E_URL}
                        fi
                        
                        echo "skipping license check"
                        '''
            }
        }
        stage('Get nightwatch XSL and add screenshots directory') {
            steps{
                sh '''#!/bin/bash
                        curl -o nightwatchxsl.xsl https://gist.githubusercontent.com/unlikelyzero/164f03df3bf4ee2b01ee8c263979051b/raw/8b3356e2a1e059bef6ec64ac7e9a16566f5f550e/nightwatchxsl.xsl
                        mkdir -p awx/ui/test/e2e/screenshots
                        '''
            }
        }
        stage('Get Docker image') {
            steps{
                withCredentials([file(credentialsId: '86ed99e9-dad9-49e9-b0db-9257fb563bad', variable: 'JSON_KEY_FILE')]) {
                    withEnv(["JSON_KEY_FILE=${JSON_KEY_FILE}"]) {
                        sshagent(['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                            sh '''#!/bin/bash
                            docker login -u _json_key -p "$(cat "${JSON_KEY_FILE}")" https://gcr.io
                            docker pull gcr.io/ansible-tower-engineering/tower_e2e:latest
                            docker tag gcr.io/ansible-tower-engineering/tower_e2e:latest tower_e2e:latest
                            '''
                        }
                    }
                 }
            }
        }
        stage('Execute docker-compose') {
            steps{
                withCredentials([string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}"]) {
                        sh '''#!/bin/bash
                                [[ -z ${AWX_E2E_PASSWORD} ]] && AWX_E2E_PASSWORD=${AWX_ADMIN_PASSWORD}
                                echo ${AWX_E2E_PASSWORD}
                                docker-compose -f awx/ui/test/e2e/cluster/docker-compose.yml run \
                                  -e AWX_E2E_URL=${AWX_E2E_URL} \
                                  -e AWX_E2E_USERNAME=${AWX_E2E_USERNAME} \
                                  -e AWX_E2E_PASSWORD=${AWX_E2E_PASSWORD} \
                                  -e AWX_E2E_SCREENSHOTS_ENABLED=true \
                                  -e AWX_E2E_SCREENSHOTS_PATH=/awx/awx/ui/test/e2e/screenshots \
                                  e2e --filter="${TEST_SELECTION}"                        
                            '''
                    }
                }
            }
        }
    }
    post {
        always {
            xunit reduceLog: false, testTimeMargin: '15000', thresholds: [failed(failureThreshold: '1'), skipped(failureThreshold: '1')], tools: [Custom(customXSL: 'nightwatchxsl.xsl', deleteOutputFiles: false, failIfNotNew: false, pattern: 'awx/ui/test/e2e/reports/*.xml', skipNoTestFiles: false, stopProcessingIfError: true)]
            archiveArtifacts 'awx/ui/test/e2e/reports/*.xml,awx/ui/test/e2e/screenshots/**'
        }
    }
}
