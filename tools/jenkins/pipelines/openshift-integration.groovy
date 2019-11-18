pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.6.1', '3.6.0',
                      '3.5.4', '3.5.3', '3.5.2', '3.5.1', '3.5.0',
                      '3.4.6', '3.4.5', '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.8', '3.3.7', '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0']
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
            name: 'TESTEXPR',
            description: 'Specify the TESTEXPR to pass to pytest if necessary',
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
        timeout(time: 18, unit: 'HOURS')
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
                withCredentials([file(credentialsId: 'abcd0260-fb83-404e-860f-f9697911a0bc', variable: 'VAULT_FILE'),
                                 string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["SCENARIO=openshift",
                             "OPENSHIFT_PASS=${AWX_ADMIN_PASSWORD}",
                             "AWX_USE_TLS=${AWX_USE_TLS}",
                             "AW_REPO_URL=${AW_REPO_URL}",
                             "AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}",
                             "TOWER_VERSION=${params.TOWER_VERSION}"]) {
                        sh 'ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml'
                        sh './tools/jenkins/scripts/generate_vars.sh'
                    }
                }
            }
        }

        stage ('Install') {
            steps {
                withCredentials([string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["OPENSHIFT_PASS=${AWX_ADMIN_PASSWORD}",
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

        stage ('Integration Tests') {
            steps {
                withEnv(["TESTEXPR=${TESTEXPR}", "OPENSHIFT_PROJECT=${OPENSHIFT_PROJECT}"]) {
                    sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                        sh './tools/jenkins/scripts/test.sh'
                        sh 'cp reports/junit/results-final.xml artifacts/results.xml'
                        junit 'artifacts/results.xml'
                    }
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
                    script {
                        OPENSHIFT_PROJECT = readFile('artifacts/openshift_project').trim()
                    }
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
