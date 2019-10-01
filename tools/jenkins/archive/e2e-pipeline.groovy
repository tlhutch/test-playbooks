pipeline {
    agent {
        label 'jenkins-jnlp-agent'
    }
    triggers {
        pollSCM('H */2 * * *')
    }
    options {
        disableConcurrentBuilds()
        timeout(time: 2, unit: 'HOURS')
        timestamps()
    }
    stages {
        stage('Build in parallel') {
            failFast true
            parallel {
                stage('Checkout Tower 3.3') {
                    steps {
                        checkout([
                            $class: 'GitSCM',
                            branches: [
                                [ name: 'release_3.3.1' ]
                            ],
                            doGenerateSubmoduleConfigurations: false,
                            extensions: [],
                            submoduleCfg: [],
                            userRemoteConfigs: [
                                [
                                    credentialsId: 'github-ansible-jenkins-nopassphrase',
                                    url: 'git@github.com:ansible/tower.git'
                                ]
                            ]
                        ])
                    }
                }
                stage('Trigger Build_Tower_RPM Job') {
                    steps {
                        build(
                            job: 'Build_Tower_RPM',
                            parameters: [
                                booleanParam(name: 'TRIGGER', value: false),
                                string(name: 'OFFICIAL', value: 'no'),
                                string(name: 'TOWER_PACKAGING_BRANCH', value: 'origin/release_3.3.1'),
                            ]
                        )
                    }
                }
            }
        }
        stage('Create Tower Instance') {
            steps {
                ansibleTower(
                    towerServer: 'Internal',
                    templateType: 'workflow',
                    jobTemplate: '2334',
                    importTowerLogs: true,
                    inventory: '',
                    jobTags: '',
                    limit: '',
                    removeColor: true,
                    verbose: true,
                    credential: '',
                    extraVars: '{"instance_names": "launched-by-jenkins", "deployment_type": "release_3.3.1"}',
                )
                {
                    sh '''#!/bin/bash
                    set +e
                    TARGET_HOST=$(curl -s -f -k -L \\
                        -u "${TOWER_USERNAME}":"${TOWER_PASSWORD}" \\
                        -H "Content-Type: application/json" \\
                        -X GET \\
                        http://tower.ansible.eng.rdu2.redhat.com/api/v2/inventories/144/hosts/\\?name\\=launched-by-jenkins \\
                        | python -c \'import sys, json; print json.loads(json.load(sys.stdin)["results"][0]["variables"])["gce_public_ip"]\')
                    AWX_E2E_URL=https://${TARGET_HOST}
                    curl --fail ${AWX_E2E_URL}
                    echo ${AWX_E2E_URL} > AWX_E2E_URL.properties'''
                }
                stash('AWX_E2E_URL.properties')
            }
        }
        stage('Run E2E Tests') {
            steps{
                unstash('AWX_E2E_URL.properties')
                script {
                    AWX_E2E_URL = readFile 'AWX_E2E_URL.properties'
                }
                echo "Running e2e tests against ${AWX_E2E_URL}"
                retry(2) {
                    build(
                        job: 'Test_Tower_E2E',
                        parameters: [
                            string(name: 'AWX_E2E_URL', value: "${AWX_E2E_URL}"),
                            string(name: 'TOWER_REPO', value: 'git@github.com:ansible/tower.git')
                            string(name: 'TOWER_BRANCH_NAME', value: 'release_3.3.1')
                        ]
                    )
                }
            }
            post {
                always {
                    copyArtifacts(
                        filter: 'awx/ui/test/e2e/reports/*.xml',
                        fingerprintArtifacts: true,
                        projectName: "Test_Tower_E2E",
                        selector: lastCompleted()
                    )
                    junit('awx/ui/test/e2e/reports/*.xml')
                }
            }
        }
    }
    post {
        success {
            slackSend(
                color: "good",
                teamDomain: "ansible",
                channel: "#e2e-test-resuts",
                message: "<$JENKINS_BLUE_URL$JOB_NAME/detail/$JOB_NAME/$BUILD_NUMBER|Success!>"
            )
        }
        failure {
            slackSend(
                color: "bad",
                teamDomain: "ansible",
                channel: "#e2e-test-resuts",
                message: "<$JENKINS_BLUE_URL$JOB_NAME/detail/$JOB_NAME/$BUILD_NUMBER|SHAME!>"
            )
        }
        fixed {
            slackSend(
                color: "good",
                teamDomain: "ansible",
                channel: "#ui-talk",
                message: "<$JENKINS_BLUE_URL$JOB_NAME/detail/$JOB_NAME/$BUILD_NUMBER|Back to Success>"
            )
        }
        always {
            step([$class: 'InfluxDbPublisher', jenkinsEnvParameterTag: 'job_name=${JOB_NAME}', target: 'openshift'])
            slackSend(
                color: "good",
                teamDomain: "ansible",
                channel: "#e2e-test-resuts",
                message: "<$JENKINS_BLUE_URL$JOB_NAME/detail/$JOB_NAME/$BUILD_NUMBER|Job Dun>"
            )
        }
    }
}

