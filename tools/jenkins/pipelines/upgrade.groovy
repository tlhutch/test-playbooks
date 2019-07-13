pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION_TO_UPGRADE_FROM',
            description: 'Tower version to upgrade from ?',
            choices: ['3.5.0', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0',
                      '3.2.8']
        )
        choice(
            name: 'TOWER_VERSION_TO_UPGRADE_TO',
            description: 'Tower version to upgrade to ?',
            choices: ['devel', '3.5.1', '3.5.0',
                      '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0',
                      '3.2.8', '3.2.7', '3.2.6', '3.2.5', '3.2.4', '3.2.3', '3.2.2', '3.2.1', '3.2.0']
        )
        choice(
            name: 'ANSIBLE_VERSION',
            description: 'Ansible version to deploy within Tower install',
            choices: ['devel', 'stable-2.8', 'stable-2.7', 'stable-2.6', 'stable-2.5',
                      'stable-2.4', 'stable-2.3']
        )
        choice(
            name: 'SCENARIO',
            description: 'Deployment scenario for Tower install',
            choices: ['standalone', 'cluster']
        )
        choice(
            name: 'PLATFORM',
            description: 'The OS to install the Tower instance on',
            choices: ['rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'rhel-8.0-x86_64', 'ol-7.6-x86_64', 'centos-7.latest-x86_64',
                      'ubuntu-16.04-x86_64', 'ubuntu-14.04-x86_64']
        )
        choice(
            name: 'BUNDLE',
            description: 'Should the bundle version be used ?',
            choices: ['no', 'yes']
        )
        choice(
            name: 'AWX_IPV6_DEPLOYMENT',
            description: 'Should the deployment use IPv6 ?',
            choices: ['no', 'yes']
        )
        string(
            name: 'TOWERQA_BRANCH',
            description: 'ansible/tower-qa branch to use (Empty will do the right thing)',
            defaultValue: ''
        )
        string(
            name: 'DEPLOYMENT_NAME',
            description: 'Deployment name. Will match VM name being spawned in the cloud',
            defaultValue: 'evergreen-jenkins-tower-upgrade'
        )
        choice(
            name: 'VERBOSE',
            description: 'Should the deployment be verbose ?',
            choices: ['no', 'yes']
        )
        choice(
            name: 'OUT_OF_BOX_OS',
            description: 'Should the deployment be made on a vanilla OS (ie. no prev preparation will take place) ?',
            choices: ['no', 'yes']
        )
        choice(
            name: 'FROM_STAGE',
            description: 'Should the installs and RPM be pulled from staging environment ?',
            choices: ['no', 'yes']
        )
        choice(
            name: 'CLEAN_DEPLOYMENT_BEFORE_JOB_RUN',
            description: 'Should the deployment be cleaned before job is run ?',
            choices: ['yes', 'no']
        )
        choice(
            name: 'CLEAN_DEPLOYMENT_AFTER_JOB_RUN',
            description: 'Should the deployment be cleaned after job is run ?',
            choices: ['no', 'yes']
        )
        choice(
            name: 'CLEAN_DEPLOYMENT_ON_JOB_FAILURE',
            description: 'Should the deployment be cleaned if job fails ?',
            choices: ['yes', 'no']
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
echo """Tower Version to upgrade from: ${params.TOWER_VERSION_TO_UPGRADE_FROM}
Tower Version to upgrade to: ${params.TOWER_VERSION_TO_UPGRADE_TO}
Ansible Version under test: ${params.ANSIBLE_VERSION}
Platform under test: ${params.PLATFORM}
Scenario: ${params.SCENARIO}
Bundle?: ${params.BUNDLE}"""
            }
        }

        stage('Checkout tower-qa') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/release_${params.TOWER_VERSION_TO_UPGRADE_FROM}" ]],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'd2d4d16b-dc9a-461b-bceb-601f9515c98a',
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
                                 string(credentialsId: 'aws_access_key', variable: 'AWS_ACCESS_KEY'),
                                 string(credentialsId: 'aws_secret_key', variable: 'AWS_SECRET_KEY'),
                                 string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["AWS_SECRET_KEY=${AWS_SECRET_KEY}",
                             "AWS_ACCESS_KEY=${AWS_ACCESS_KEY}",
                             "AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}",
                             "TOWER_VERSION=${params.TOWER_VERSION_TO_UPGRADE_FROM}",
                             "AWX_APPLY_ISOLATED_GROUPS_FW_RULES=false"]) {
                        sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                            sh 'mkdir -p ~/.ssh && cp ${PUBLIC_KEY} ~/.ssh/id_rsa.pub'
                            sh 'ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials.vault --output=config/credentials.yml'
                            sh 'ansible-vault decrypt --vault-password-file="${VAULT_FILE}" config/credentials-pkcs8.vault --output=config/credentials-pkcs8.yml || true'

                            // Generate variable file for test runner
                            sh 'SCENARIO=test_runner ./tools/jenkins/scripts/generate_vars.sh'

                            // Generate variable file for tower deployment
                            sh './tools/jenkins/scripts/generate_vars.sh'

                            sh 'ansible-playbook -v -i playbooks/inventory -e @playbooks/test_runner_vars.yml playbooks/deploy-test-runner.yml'

                            // Archive test runner inventory file and show it to user so they can optionally shell in
                            sh 'mkdir -p artifacts'
                            sh 'cat playbooks/inventory.test_runner | tee artifacts/inventory.test_runner'
                            sh 'grep -A 1 test-runner playbooks/inventory.test_runner | tail -n 1 | cut -d" " -f1 > artifacts/test_runner_host'

                            sh "ansible test-runner -i playbooks/inventory.test_runner -m git -a 'repo=git@github.com:ansible/tower-qa version=release_${params.TOWER_VERSION_TO_UPGRADE_FROM} dest=tower-qa ssh_opts=\"-o StrictHostKeyChecking=no\" force=yes'"
                        }
                    }
                }
            }
        }

        stage ('Install') {
            steps {
               sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                   sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_install.yml'
                }
            }
        }

        stage ('Load data') {
            steps {
               sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                   sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_load.yml'
                }
            }
        }

        stage('Clean cache and newer tower-qa') {
            steps {
               script {
                   if (params.TOWERQA_BRANCH == '') {
                       if (params.TOWER_VERSION_TO_UPGRADE_TO == 'devel') {
                           branch_name = 'devel'
                       } else {
                           branch_name = "release_${params.TOWER_VERSION_TO_UPGRADE_TO}"
                       }
                   } else {
                       branch_name = params.TOWERQA_BRANCH
                   }
               }
                withCredentials([string(credentialsId: 'aws_access_key', variable: 'AWS_ACCESS_KEY'),
                                 string(credentialsId: 'aws_secret_key', variable: 'AWS_SECRET_KEY'),
                                 string(credentialsId: 'awx_admin_password', variable: 'AWX_ADMIN_PASSWORD')]) {
                    withEnv(["AWS_SECRET_KEY=${AWS_SECRET_KEY}",
                             "AWS_ACCESS_KEY=${AWS_ACCESS_KEY}",
                             "AWX_ADMIN_PASSWORD=${AWX_ADMIN_PASSWORD}",
                             "TOWER_VERSION=${params.TOWER_VERSION_TO_UPGRADE_TO}",
                             "AWX_UPGRADE=true",
                             "CLEAN_DEPLOYMENT_BEFORE_JOB_RUN=no"]) {
                        sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                            sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_clean_cache.yml'
                            sh './tools/jenkins/scripts/generate_vars.sh'
                            sh "ansible test-runner -i playbooks/inventory.test_runner -m copy -a 'src=playbooks/vars.yml dest=/home/ec2-user/tower-qa/playbooks/vars.yml'"
                            sh "ansible test-runner -i playbooks/inventory.test_runner -m git -a 'repo=git@github.com:ansible/tower-qa version=${branch_name} dest=tower-qa ssh_opts=\"-o StrictHostKeyChecking=no\" force=yes'"
                        }
                    }
                }
            }
        }

        stage ('Upgrade') {
            steps {
               sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                   sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_install.yml'

                   // NOTE(spredzy): To change cleanly
                   sh "ansible test-runner -i playbooks/inventory.test_runner -a 'sed -i \"s/delete_on_start: .*/delete_on_start: true/g\" /home/ec2-user/tower-qa/playbooks/vars.yml'"
                }
            }
        }

        stage ('Verify data integrity') {
            steps {
               sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                   sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_verify.yml'
                }
            }
        }

    }

    post {
        always {
            sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_fetch_artifacts.yml'
            }
            archiveArtifacts artifacts: 'artifacts/*'
        }

        cleanup {
            sshagent(credentials : ['d2d4d16b-dc9a-461b-bceb-601f9515c98a']) {
                sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_cleanup.yml'
                sh 'ansible-playbook -v -i playbooks/inventory -e @playbooks/test_runner_vars.yml playbooks/reap-tower-ec2.yml'
            }
        }
    }
}
