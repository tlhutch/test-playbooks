pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION_TO_UPGRADE_FROM',
            description: 'Tower version to upgrade from ?',
            choices: ['3.6.2', '3.6.1', '3.6.0',
                      '3.5.4', '3.5.3', '3.5.2', '3.5.1', '3.5.0', '3.4.5', '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.7', '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0',
                      '3.2.8']
        )
        choice(
            name: 'TOWER_VERSION_TO_UPGRADE_TO',
            description: 'Tower version to upgrade to ?',
            choices: ['devel', '3.6.3', '3.6.2', '3.6.1', '3.6.0',
                      '3.5.5', '3.5.4', '3.5.3', '3.5.2', '3.5.1', '3.5.0',
                      '3.4.6', '3.4.5', '3.4.4', '3.4.3', '3.4.2', '3.4.1', '3.4.0',
                      '3.3.8', '3.3.7', '3.3.6', '3.3.5', '3.3.4', '3.3.3', '3.3.2', '3.3.1', '3.3.0',
                      '3.2.8', '3.2.7', '3.2.6', '3.2.5', '3.2.4', '3.2.3', '3.2.2', '3.2.1', '3.2.0']
        )
        choice(
            name: 'ANSIBLE_VERSION',
            description: 'Ansible version to deploy within Tower install',
            choices: ['devel', 'stable-2.9', 'stable-2.8', 'stable-2.7', 'stable-2.6', 'stable-2.5',
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
            choices: ['rhel-7.7-x86_64', 'rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'rhel-8.1-x86_64', 'rhel-8.0-x86_64', 'centos-7.latest-x86_64',
                      'ubuntu-16.04-x86_64', 'ubuntu-14.04-x86_64']
        )
        choice(
            name: 'AWX_USE_FIPS',
            description: 'Should FIPS be enabled for this deployment ?',
            choices: ['no', 'yes']
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
        choice(
            name: 'UPDATE_QE_DASHBOARD',
            description: 'Should the results of this run be sent to the QE dashboard ?',
            choices: ['no', 'yes']
        )
    }

    options {
        timestamps()
        timeout(time: 3, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '10'))
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
                             "AWX_USE_FIPS=${AWX_USE_FIPS}",
                             "TOWER_VERSION=${params.TOWER_VERSION_TO_UPGRADE_FROM}",
                             "ANSIBLE_FORCE_COLOR=true",
                             "AWX_APPLY_ISOLATED_GROUPS_FW_RULES=false"]) {
                        sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                            sh './tools/jenkins/scripts/prep_test_runner.sh'
                            sh "ansible test-runner -i playbooks/inventory.test_runner -m git -a 'repo=git@github.com:ansible/tower-qa version=release_${params.TOWER_VERSION_TO_UPGRADE_FROM} dest=tower-qa ssh_opts=\"-o StrictHostKeyChecking=no\" force=yes'"
                        }
                    }
                }

                script {
                    TEST_RUNNER_HOST = readFile('artifacts/test_runner_host').trim()
                    SSH_OPTS = '-o ForwardAgent=yes -o StrictHostKeyChecking=no'
                    ORIGINAL_INSTANCE_NAME_PREFIX = sh(script: 'grep instance_name_prefix playbooks/vars.yml | cut -d" " -f2', returnStdout: true).trim()
                }
            }
        }

        stage ('Install') {
            steps {
                withEnv(["ANSIBLE_FORCE_COLOR=true"]) {
                    sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                        sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/install.sh'"
                    }
                }
            }
        }

        stage ('Load data') {
            steps {
               sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                   sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/load.sh'"
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
                        sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                            sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/clean_cache.sh'"
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
                withEnv(["ANSIBLE_FORCE_COLOR=true"]) {
                    sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                        sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/install.sh'"
                        sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'sed -i \"s/instance_name_prefix.*/instance_name_prefix: ${ORIGINAL_INSTANCE_NAME_PREFIX}/g\" tower-qa/playbooks/vars.yml'"

                        // NOTE(spredzy): To change cleanly
                        sh "ansible test-runner -i playbooks/inventory.test_runner -a 'sed -i \"s/delete_on_start: .*/delete_on_start: true/g\" /home/ec2-user/tower-qa/playbooks/vars.yml'"
                    }
                }
            }
        }

        stage ('Verify data integrity') {
            steps {
               sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                   sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/verify.sh'"
                }
            }
        }

    }

    post {
        always {
            sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/collect.sh' || true"
                sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_fetch_artifacts_tower.yml || true'
                sh 'ansible-playbook -v -i playbooks/inventory.test_runner playbooks/test_runner/run_fetch_artifacts.yml'
            }
            archiveArtifacts allowEmptyArchive: true, artifacts: 'artifacts/*'
            node('jenkins-jnlp-agent') {
                script {
                    is_major = params.TOWER_VERSION_TO_UPGRADE_TO[0] > params.TOWER_VERSION_TO_UPGRADE_FROM[0] || params.TOWER_VERSION_TO_UPGRADE_TO[2] > params.TOWER_VERSION_TO_UPGRADE_FROM[2]
                    if (is_major) {
                        component = 'major_upgrade'
                    } else {
                        component = 'minor_upgrade'
                    }
                    json = "{\"tower\":\"${params.TOWER_VERSION_TO_UPGRADE_TO}\", \"bundle\":\"${params.BUNDLE}\", \"url\": \"${env.RUN_DISPLAY_URL}\", \"component\":\"${component}\", \"status\":\"${currentBuild.result}\", \"tls\":\"no\", \"fips\":\"${params.AWX_USE_FIPS}\", \"deploy\":\"${params.SCENARIO}\", \"platform\":\"${params.PLATFORM}\", \"ansible\":\"${params.ANSIBLE_VERSION}\"}"
                }
                sh "test ${params.UPDATE_QE_DASHBOARD} = 'yes' && curl -v -X POST 'http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/sign_off_jobs' -H 'Content-type: application/json' -d '${json}' || echo 'Not updating dashboard for this run'"
            }
        }

        cleanup {
            sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/cleanup.sh'"
                sh 'ansible-playbook -v -i playbooks/inventory -e @playbooks/test_runner_vars.yml playbooks/reap-tower-ec2.yml'
            }
        }
    }
}
