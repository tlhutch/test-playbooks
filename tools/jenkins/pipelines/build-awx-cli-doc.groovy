pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.6.2' , '3.6.1', '3.6.0']
        )
        string(
            name: 'TOWER_PACKAGING_FORK',
            description: 'Fork of tower-packaging to deploy',
            defaultValue: 'ansible'
        )
        string(
            name: 'TOWER_PACKAGING_BRANCH',
            description: 'Branch to use for tower-packaging (Empty will do the right thing)',
            defaultValue: ''
        )
    }

    options {
        timestamps()
        timeout(time: 3, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage('Build Information') {
            steps {
                echo "Tower Version under test: ${params.TOWER_VERSION}"

                script {
                    product_docs_branch_name = params.TOWER_VERSION == 'devel' ? 'master' : "release_${params.TOWER_VERSION}"
                }
            }
        }

        stage('Checkout tower-qa') {
            steps {
                script {
                    branch_name = params.TOWER_VERSION == 'devel' ? 'devel' : "release_${params.TOWER_VERSION}"
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

        stage('Deploy test-runner node') {
            steps {
                withCredentials([file(credentialsId: '171764d8-e57c-4332-bff8-453670d0d99f', variable: 'PUBLIC_KEY'),
                                 file(credentialsId: 'abcd0260-fb83-404e-860f-f9697911a0bc', variable: 'VAULT_FILE'),
                                 file(credentialsId: '86ed99e9-dad9-49e9-b0db-9257fb563bad', variable: 'JSON_KEY_FILE'),
                                 string(credentialsId: 'aws_access_key', variable: 'AWS_ACCESS_KEY'),
                                 string(credentialsId: 'aws_secret_key', variable: 'AWS_SECRET_KEY'),
                                 string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["AWS_SECRET_KEY=${AWS_SECRET_KEY}",
                             "AWS_ACCESS_KEY=${AWS_ACCESS_KEY}",
                             "AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}",
                             "ANSIBLE_FORCE_COLOR=true"]) {
                        sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                            sh './tools/jenkins/scripts/prep_test_runner.sh'
                            sh "ansible test-runner -i playbooks/inventory.test_runner -m git -a 'repo=git@github.com:ansible/tower-qa version=${branch_name} dest=tower-qa ssh_opts=\"-o StrictHostKeyChecking=no\" force=yes'"
                        }
                    }
                }

                script {
                    TEST_RUNNER_HOST = readFile('artifacts/test_runner_host').trim()
                    SSH_OPTS = '-o ForwardAgent=yes -o StrictHostKeyChecking=no'
                }
            }
        }

        stage ('Install') {
            steps {
                withEnv(["ANSIBLE_FORCE_COLOR=true"]) {
                    sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                        // Use SSH this way so we can get live feed of output on jenkins
                        sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/install.sh'"
                        sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_fetch_artifacts.yml'
                    }
                }

                script {
                    TOWER_URL = readFile('artifacts/tower_url').trim()
                }
            }
        }

        stage ('Generate the documentation') {
            steps {
                script {
                    if (params.TOWER_PACKAGING_BRANCH == '') {
                        packaging_branch_name = params.TOWER_VERSION == 'devel' ? 'devel' : "release_${params.TOWER_VERSION}"
                    } else {
                        packaging_branch_name = params.TOWER_PACKAGING_BRANCH
                    }
                }
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${packaging_branch_name}" ]],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'github-ansible-jenkins-nopassphrase',
                            url: "git@github.com:${params.TOWER_PACKAGING_FORK}/tower-packaging.git"
                        ]
                    ]
                ])
                script {
                    sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                        sh "yum install -y libyaml-devel"
                        sh """
ansible-playbook -i tools/ansible/inventory tools/ansible/build-awx-cli-docs.yml -v \
  -e tower_host=$TOWER_URL \
  -e tower_username=admin \
  -e tower_password=fo0m4nchU \
  -e tower_branch=$branch_name \
  -e product_docs_branch=$product_docs_branch_name
"""
                    }
                }
            }
        }

        stage ('Synchronize documentation') {
            steps {
                sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                    sh "ansible-playbook -i tools/ansible/inventory tools/ansible/publish-awx-cli-docs.yml -v"
                }
            }
        }
    }

    post {
        cleanup {
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

            script {
                sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                    sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/cleanup.sh'"
                    sh 'ansible-playbook -v -i playbooks/inventory -e @playbooks/test_runner_vars.yml playbooks/reap-tower-ec2.yml'
                }
            }
        }
    }

}
