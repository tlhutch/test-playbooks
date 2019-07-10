pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        string(
            name: 'RHEL_COMPOSE_ID',
            description: 'RHEL Compose Id to test',
        )
        string(
            name: 'RHEL_IMAGE_NAME',
            description: 'RHEL Image Name on OpenStack (if diffent than RHEL_COMPOSE_ID)',
            defaultValue: '${RHEL_COMPOSE_ID}'
        )
        string(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            defaultValue: 'devel'
        )
    }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage ('Pipeline Information') {
            steps {
                echo """Compose ID: ${params.RHEL_COMPOSE_ID}
Tower Version: ${params.TOWER_VERSION}"""
            }
        }

        stage ('Setup Platform - Prereq') {
            steps {
                withCredentials([file(credentialsId: '171764d8-e57c-4332-bff8-453670d0d99f', variable: 'PUBLIC_KEY'),
                                 file(credentialsId: 'abcd0260-fb83-404e-860f-f9697911a0bc', variable: 'VAULT_FILE'),
                                 string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["OUT_OF_BOX=yes", "AWS_SECRET_KEY=DUMMY", "AWS_ACCESS_KEY=DUMMY",
                             "ANSIBLE_INSTALL_METHOD=none",
                             "AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}", "TOWER_VERSION=${params.TOWER_VERSION}"]) {
                        sh 'pip install -U openstackclient'
                        sh 'mkdir -p ~/.ssh && cp ${PUBLIC_KEY} ~/.ssh/id_rsa.pub'
                        sh 'ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml'
                        sh './tools/jenkins/scripts/generate_vars.sh && source /home/jenkins/venvs/venv/bin/activate && deactivate'
                    }
                }
            }
        }

        stage ('Deploy RHEL VM') {
            steps {
                withCredentials([string(credentialsId: 'f0e7830e-477f-483c-b7b1-55c3704a6307', variable: 'OS_PASSWORD')]) {
                    withEnv(["OS_PASSWORD=${OS_PASSWORD}",
                             "OS_AUTH_URL=https://rhos-d.infra.prod.upshift.rdu2.redhat.com:13000/v3",
                             "OS_PROJECT_ID=0ac6ff23baf344e78d6f81fb5d5b2aa8",
                             "OS_PROJECT_NAME=ansible-tower",
                             "OS_USER_DOMAIN_NAME=redhat.com",
                             "OS_PROJECT_DOMAIN_ID=62cf1b5ec006489db99e2b0ebfb55f57",
                             "OS_USERNAME=yguenane",
                             "OS_REGION_NAME=regionOne",
                             "OS_ENDPOINT_TYPE=publicURL",
                             "OS_IDENTITY_API_VERSION=3"]) {
                        sh "ansible-playbook playbooks/lptesting.yml -e rhel_compose_id=${params.RHEL_COMPOSE_ID} -e tower_version=${params.TOWER_VERSION} -e rhel_image_name=${RHEL_IMAGE_NAME} --tags deploy"
                    }
                }
                archiveArtifacts artifacts: 'playbooks/inventory.lptesting'
            }
        }

        stage ('Prepare RHEL Tower node') {
            steps {
                withCredentials([string(credentialsId: '59bf4b91-d28d-4ca1-a21d-cc26112e8725', variable: 'ACCESS_PASSWORD')]) {
                    sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                        sh "ansible-playbook -i playbooks/inventory.lptesting playbooks/lptesting.yml -e tower_version=${params.TOWER_VERSION} -e red_hat_username='yguenane@redhat.com' -e rhel_compose_id=${params.RHEL_COMPOSE_ID} -e red_hat_password='${ACCESS_PASSWORD}' --tags prepare"
                    }
                }
            }
        }

        stage ('Install Tower') {
            steps {
                sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                    sh 'ansible-playbook -i playbooks/inventory.lptesting playbooks/lptesting.yml -e @playbooks/vars.yml --tags install'
                }
            }
        }

        stage('Checkout tower-qa') {
            steps {
                script {
                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.TOWER_VERSION}"
                    }
                }
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${branch_name}" ]],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'd2d4d16b-dc9a-461b-bceb-601f9515c98a',
                            url: 'git@github.com:ansible/tower-qa.git'
                        ]
                    ]
                ])
            }
        }

        stage ('Test Tower') {
            steps {
                withEnv(['INVENTORY=playbooks/inventory.lptesting',
                         'TESTEXPR=test_utf8']) {
                    sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                        sh './tools/jenkins/scripts/test.sh'
                        junit 'reports/junit/results-final.xml'
                        archiveArtifacts 'reports/junit/results-final.xml'
                    }
                }
            }
        }
    }
}
