pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.6.2', '3.6.1', '3.6.0',
                      '3.5.4', '3.5.3', '3.5.2', '3.5.1', '3.5.0',
                      '3.4.6', '3.4.5', '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.8', '3.3.7', '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0']
        )
        choice(
            name: 'ANSIBLE_VERSION',
            description: 'Ansible version to run the install playbooks with. (NOTE: The version within the container might be different)',
            choices: ['devel', 'stable-2.9', 'stable-2.8', 'stable-2.7']
        )
        string(
            name: 'AW_REPO_URL',
            description: 'Specify the URL of the OpenShift Installer (Empty will pull the proper one based on TOWER_VERSION)',
            defaultValue: ''
        )
        choice(
            name: 'AWX_USE_TLS',
            description: 'Should RabbitMQ be deployed with TLS enabled (certificates are generated on the fly)',
            choices: ['no', 'yes']
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
        string(
            name: 'PG_HOSTNAME',
            description: 'Provide a database host. If none provided, an ephemeral database will be created in openshift.',
            defaultValue: ''
        )
        string(
            name: 'PG_PORT',
            description: 'Provide the database port if using pre-configured database with PG_HOST',
            defaultValue: ''
        )
        string(
            name: 'PG_DATABASE',
            description: 'Provide the name of the database in the postgres instance if using pre-configured database with PG_HOST',
            defaultValue: ''
        )
        string(
            name: 'PG_USERNAME',
            description: 'Override default database user. If nothing provided, default will be used.',
            defaultValue: ''
        )
        string(
            name: 'PG_PASSWORD',
            description: 'Override default database user password. If nothing provided, default will be used.',
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
        buildDiscarder(logRotator(daysToKeepStr: '10'))
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
                withCredentials([string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD'),
                                 string(credentialsId: 'jenkins_password_ocp3_ansible_eng', variable: 'OPENSHIFT_PASS'),
                                 string(credentialsId: 'jenkins_token_ocp3_ansible_eng', variable: 'OPENSHIFT_TOKEN')]) {
                    withEnv(["SCENARIO=openshift",
                             "OPENSHIFT_TOKEN=${OPENSHIFT_TOKEN}",
                             "OPENSHIFT_PASS=${OPENSHIFT_PASS}",
                             "AWX_USE_TLS=${AWX_USE_TLS}",
                             "AW_REPO_URL=${AW_REPO_URL}",
                             "AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}",
                             "ANSIBLE_INSTALL_METHOD=pip",
                             "TOWER_VERSION=${params.TOWER_VERSION}"]) {
                        sh './tools/jenkins/scripts/generate_vars.sh'
                    }
                }
            }
        }

        stage ('Install') {
            steps {
                withCredentials([string(credentialsId: 'jenkins_token_ocp3_ansible_eng', variable: 'OPENSHIFT_TOKEN'),
                                 string(credentialsId: 'jenkins_password_ocp3_ansible_eng', variable: 'OPENSHIFT_PASS')]) {
                    withEnv(["OPENSHIFT_PASS=${OPENSHIFT_PASS}",
                             "OPENSHIFT_TOKEN=${OPENSHIFT_TOKEN}",
                             "PG_PASSWORD=${PG_PASSWORD}",
                             "PG_HOSTNAME=${PG_HOSTNAME}",
                             "PG_USERNAME=${PG_USERNAME}",
                             "PG_DATABASE=${PG_DATABASE}",
                             "PG_PORT=${PG_PORT}",
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
            node('jenkins-jnlp-agent') {
                script {
                    if (params.AWX_USE_TLS == 'true') {
                        tls = 1
                    } else {
                        tls = 0
                    }
                    json = "{\"tower\":\"${params.TOWER_VERSION}\", \"url\": \"${env.RUN_DISPLAY_URL}\", \"component\":\"install\", \"status\":\"${currentBuild.result}\", \"tls\":\"${tls}\", \"deploy\":\"cluster\", \"platform\":\"OpenShift\", \"ansible\":\"${params.ANSIBLE_VERSION}\""
                }
                sh "curl -v -X POST 'http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/sign_off_jobs' -H 'Content-type: application/json' -d '${json}'"
            }
        }
        cleanup {
            script {
                if (params.CLEAN_DEPLOYMENT_AFTER_JOB_RUN == 'yes') {
                    script {
                        OPENSHIFT_PROJECT = readFile('artifacts/openshift_project').trim()
                    }
                    withCredentials([string(credentialsId: 'jenkins_token_ocp3_ansible_eng', variable: 'OPENSHIFT_TOKEN'),
                                     string(credentialsId: 'jenkins_password_ocp3_ansible_eng', variable: 'OPENSHIFT_PASS')]) {
                        withEnv(["OPENSHIFT_PASS=${OPENSHIFT_PASS}",
                                 "OPENSHIFT_TOKEN=${OPENSHIFT_TOKEN}",
                                 "OPENSHIFT_PROJECT=${OPENSHIFT_PROJECT}"]) {
                            sh './tools/jenkins/scripts/openshift_cleanup.sh'
                        }
                    }
                }
            }
        }
    }
}
