pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.5.4', '3.5.3', '3.5.2', '3.5.1', '3.5.0',
                      '3.4.6', '3.4.5', '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.8', '3.3.7', '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0']
        )
        string(
            name: 'TOWERQA_BRANCH',
            description: 'ansible/tower-qa branch to use (Empty will do the right thing)',
            defaultValue: ''
        )
        string(
            name: 'TOWER_CONTAINER_IMAGE',
            description: 'Override the URL from which the Tower container image will be pulled from. (Empty will pull the proper one based on TOWER_VERSION)',
            defaultValue: ''
        )
        string(
            name: 'MESSAGING_CONTAINER_IMAGE',
            description: 'Override the URL from which the Tower Messaging container image will be pulled from. (Empty will pull the proper one based on TOWER_VERSION)',
            defaultValue: ''
        )
        string(
            name: 'MEMCACHED_CONTAINER_IMAGE',
            description: 'Override the URL from which the Tower Memcached container image will be pulled from. (Empty will pull the proper one based on TOWER_VERSION)',
            defaultValue: ''
        )
        choice(
            name: 'CLEAN_DEPLOYMENT_AFTER_JOB_RUN',
            description: 'Should the deployment be removed after job is run ?',
            choices: ['yes', 'no']
        )
    }

    options {
        timestamps()
        timeout(time: 2, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage('Build Information') {
            steps {
                echo """Tower Version under test: ${params.TOWER_VERSION}
ansible/tower-qa branch: ${params.TOWERQA_BRANCH}
Tower Container Image: ${params.TOWER_CONTAINER_IMAGE}
Tower Messaging Container Image: ${params.MESSAGING_CONTAINER_IMAGE}
Tower Memcached Container Image: ${params.MEMCACHED_CONTAINER_IMAGE}"""
            }
        }

        stage('Checkout tower-qa') {
            steps {
                script {
                    if (params.TOWERQA_BRANCH == '') {
                        branch_name = params.TOWER_VERSION == 'devel' ? 'devel' : "release_${params.TOWER_VERSION}"
                    } else {
                        branch_name = params.TOWERQA_BRANCH
                    }
                }
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${branch_name}" ]],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'github-ansible-jenkins-nopassphrase',
                            url: 'git@github.com:ansible/tower-qa.git'
                        ]
                    ]
                ])
            }
        }

        stage('Prepare Environment') {
            steps {
                withCredentials([string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["SCENARIO=openshift",
                             "OPENSHIFT_PASS=${AWX_ADMIN_PASSWORD}",
                             "AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}",
                             "TOWER_VERSION=${params.TOWER_VERSION}"]) {
                        sh './tools/jenkins/scripts/generate_vars.sh'
                    }
                }
            }
        }

        stage ('Install') {
            steps {
                withCredentials([string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["OPENSHIFT_PASS=${AWX_ADMIN_PASSWORD}",
                             "ANSIBLE_FORCE_COLOR=true"]) {
                        sh './tools/jenkins/scripts/openshift_install.sh'
                    }
                }

                script {
                    // artifacts/openshift_project gets written by tower-qa/tools/jenkins/scripts/openshift_install.sh
                    OPENSHIFT_PROJECT = readFile('artifacts/openshift_project').trim()
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts/*'
        }
        cleanup {
            script {
                if (params.CLEAN_DEPLOYMENT_AFTER_JOB_RUN == 'yes') {
                    withCredentials([string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                        withEnv(["OPENSHIFT_PASS=${AWX_ADMIN_PASSWORD}",
                                 "OPENSHIFT_PROJECT=${OPENSHIFT_PROJECT}"]) {
                            sh './tools/jenkins/scripts/openshift_cleanup.sh'
                        }
                    }
                }
            }
        }
    }
}
