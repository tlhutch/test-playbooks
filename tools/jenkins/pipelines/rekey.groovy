pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to deploy',
            choices: ['devel', '3.6.2',
                      '3.5.4']
        )
        string(
            name: 'TOWER_FORK',
            description: 'Fork of tower to deploy (Empty will do the right thing)',
            defaultValue: ''
        )
        string(
            name: 'TOWER_BRANCH',
            description: 'Branch to use for Tower (Empty will figure the branch based on the TOWER_VERSION)',
            defaultValue: ''
        )
        string(
            name: 'TOWER_PACKAGING_FORK',
            description: 'Fork of tower-packaging to deploy (Empty will do the right thing)',
            defaultValue: ''
        )
        string(
            name: 'TOWER_PACKAGING_BRANCH',
            description: 'Branch to use for tower-packaging (Empty will figure the branch based on the TOWER_VERSION)',
            defaultValue: ''
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
            name: 'AWX_USE_TLS',
            description: 'Should the network services (postgresql, rabbitmq and nginx) use TLS (with custom CA issued certificates)',
            choices: ['no', 'yes']
        )
        choice(
            name: 'AWX_USE_FIPS',
            description: 'Should FIPS be enabled for this deployment ?',
            choices: ['no', 'yes']
        )
        choice(
            name: 'PLATFORM',
            description: 'The OS to install the Tower instance on',
            choices: ['rhel-7.7-x86_64', 'rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'rhel-8.1-x86_64', 'rhel-8.0-x86_64', 'centos-7.latest-x86_64',
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
            name: 'TOWER_QA_FORK',
            description: 'Fork of tower-qa (Empty will do the right thing)',
            defaultValue: ''
        )
        string(
            name: 'TOWER_QA_BRANCH',
            description: 'tower-qa branch to use (Empty will figure the branch based on the TOWER_VERSION)',
            defaultValue: ''
        )
        string(
            name: 'DEPLOYMENT_NAME',
            description: 'Deployment name. Will match VM name being spawned in the cloud',
            defaultValue: 'evergreen-jenkins-tower-rekey'
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
            name: 'BUILD_INSTALLER_AND_PACKAGE',
            description: 'Set this to yes if you are testing any fork.',
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
        ansiColor('xterm')
        buildDiscarder(logRotator(daysToKeepStr: '10'))
        timeout(time: 3, unit: 'HOURS')
        timestamps()
    }

    stages {

        stage('Build Information') {
            steps {
                script {
                    tower_qa_fork = params.TOWER_QA_FORK
                    if (tower_qa_fork == '') {
                        tower_qa_fork = 'ansible'
                    }

                    tower_qa_branch = params.TOWER_QA_BRANCH
                    if (tower_qa_branch == '') {
                        if (params.TOWER_VERSION == 'devel') {
                            tower_qa_branch = 'devel'
                        } else {
                            tower_qa_branch = "release_${params.TOWER_VERSION}"
                        }
                    }

                    tower_fork = params.TOWER_FORK
                    if (tower_fork == '') {
                        tower_fork = 'ansible'
                    }

                    tower_branch = params.TOWER_BRANCH
                    if (tower_branch == '') {
                        if (params.TOWER_VERSION == 'devel') {
                            tower_branch = 'devel'
                        } else {
                            tower_branch = "release_${params.TOWER_VERSION}"
                        }
                    }

                    tower_packaging_fork = params.TOWER_PACKAGING_FORK
                    if (tower_packaging_fork == '') {
                        tower_packaging_fork = 'ansible'
                    }

                    tower_packaging_branch = params.TOWER_PACKAGING_BRANCH
                    if (tower_packaging_branch == '') {
                        if (params.TOWER_VERSION == 'devel') {
                            tower_packaging_branch = 'devel'
                        } else {
                            tower_packaging_branch = "release_${params.TOWER_VERSION}"
                        }
                    }

                    nightly_repo_dir = "${tower_branch}"
                    if (params.TOWER_FORK != '') {
                        nightly_repo_dir = "tower_${tower_branch}_packaging_${tower_packaging_branch}"
                    }

                    if (tower_branch == tower_packaging_branch) {
                        nightly_repo_dir = "${tower_branch}"
                    } else {
                        nightly_repo_dir = "tower_${tower_branch}_packaging_${tower_packaging_branch}"
                    }

                    if (params.PLATFORM.startsWith('rhel-8')) {
                        target_dist = 'epel-8-x86_64'
                        mock_cfg = 'rhel-8-x86_64'
                    } else {
                        target_dist = 'epel-7-x86_64'
                        mock_cfg = 'rhel-7-x86_64'
                    }
                }

                echo """\
                    Tower Version under test: ${params.TOWER_VERSION}
                    Ansible Version under test: ${params.ANSIBLE_VERSION}
                    Platform under test: ${params.PLATFORM}
                    Scenario: ${params.SCENARIO}
                    Bundle?: ${params.BUNDLE}
                    tower-qa repo info: ${tower_qa_fork}/${tower_qa_branch}
                    tower repo info: ${tower_fork}/${tower_branch}
                    tower-packaging repo info: ${tower_packaging_fork}/${tower_packaging_branch}
                    Nightly repo dir: ${nightly_repo_dir}
                    Target Dist: ${target_dist}
                    Mock cfg: ${mock_cfg}
                """.stripIndent()
            }
        }

        stage('Checkout tower-qa') {
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${tower_qa_branch}" ]],
                    userRemoteConfigs: [
                        [
                            credentialsId: 'github-ansible-jenkins-nopassphrase',
                            url: "git@github.com:${tower_qa_fork}/tower-qa.git"
                        ]
                    ]
                ])
            }
        }

        stage('Build Tower and deploy test-runner') {
            failFast true
            parallel {
                stage('Build Installer') {
                    when {
                        expression { params.BUILD_INSTALLER_AND_PACKAGE == 'yes' }
                    }

                    steps {
                        build(
                            job: 'Build_Tower_TAR',
                            parameters: [
                                string(
                                    name: 'TOWER_PACKAGING_REPO',
                                    value: "git@github.com:${tower_packaging_fork}/tower-packaging.git"
                                ),
                                string(
                                    name: 'TOWER_PACKAGING_BRANCH',
                                    value: "origin/${tower_packaging_branch}"
                                ),
                                string(
                                    name: 'TOWER_REPO',
                                    value:
                                    "git@github.com:${tower_fork}/tower.git"
                                ),
                                string(
                                    name: 'TOWER_BRANCH',
                                    value: "origin/${tower_branch}"
                                ),
                                string(
                                    name: 'NIGHTLY_REPO_DIR',
                                    value: nightly_repo_dir
                                )
                            ]
                        )
                    }
                }

                stage('Build Package') {
                    when {
                        expression { params.BUILD_INSTALLER_AND_PACKAGE == 'yes' }
                    }

                    steps {
                        script {
                            if ( params.PLATFORM.contains('ubuntu') ) {
                                PACKAGE_JOB_NAME = 'Build_Tower_DEB'
                            } else {
                                PACKAGE_JOB_NAME = 'Build_Tower_RPM'
                            }

                            build(
                                job: PACKAGE_JOB_NAME,
                                parameters: [
                                    string(
                                        name: 'TOWER_PACKAGING_REPO',
                                        value: "git@github.com:${tower_packaging_fork}/tower-packaging.git"
                                    ),
                                    string(
                                        name: 'TOWER_PACKAGING_BRANCH',
                                        value: "origin/${tower_packaging_branch}"
                                    ),
                                    string(
                                        name: 'TOWER_REPO',
                                        value:
                                        "git@github.com:${tower_fork}/tower.git"
                                    ),
                                    string(
                                        name: 'TOWER_BRANCH',
                                        value: "origin/${tower_branch}"
                                    ),
                                    string(
                                        name: 'NIGHTLY_REPO_DIR',
                                        value: nightly_repo_dir
                                    ),
                                    string(
                                        name: 'TARGET_DIST',
                                        value: target_dist
                                    ),
                                    string(
                                        name: 'MOCK_CFG',
                                        value: mock_cfg
                                    ),
                                    booleanParam(
                                        name: 'TRIGGER',
                                        value: false
                                    ),
                                ]
                            )
                        }
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
                                     "AWX_USE_TLS=${AWX_USE_TLS}",
                                     "AWX_USE_FIPS=${AWX_USE_FIPS}",
                                     "AW_REPO_URL=http://nightlies.testing.ansible.com/ansible-tower_nightlies_m8u16fz56qr6q7/${nightly_repo_dir}",
                                     "ANSIBLE_FORCE_COLOR=true"]) {
                                sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                                    sh './tools/jenkins/scripts/prep_test_runner.sh'
                                    sh 'tee artifacts/vars.yml < playbooks/vars.yml'
                                    sh "ansible test-runner -i playbooks/inventory.test_runner -m git -a 'repo=git@github.com:${tower_qa_fork}/tower-qa version=${tower_qa_branch} dest=tower-qa ssh_opts=\"-o StrictHostKeyChecking=no\" force=yes'"
                                }
                            }
                        }

                        script {
                            TEST_RUNNER_HOST = readFile('artifacts/test_runner_host').trim()
                            SSH_OPTS = '-o ForwardAgent=yes -o StrictHostKeyChecking=no'
                        }
                    }
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

        stage ('Rekey Database') {
            steps {
               sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                   sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/secret-key-check.sh'"
                   sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/rekey-test.sh'"
                   sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/rekey.sh'"
                   sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/secret-key-check.sh'"
                   sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && REKEY_CHECK=verify ./tools/jenkins/scripts/rekey-test.sh'"
                   sh "mkdir -p artifacts"
                   sh "scp ${SSH_OPTS} 'ec2-user@${TEST_RUNNER_HOST}:~/tower-qa/rekey-data.yml' artifacts"
                   sh "scp ${SSH_OPTS} 'ec2-user@${TEST_RUNNER_HOST}:~/tower-qa/reports/junit/results-rekey-*.xml' artifacts"
                   junit testResults: 'artifacts/results-rekey-*.xml'
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
        }

        cleanup {
            sshagent(credentials : ['github-ansible-jenkins-nopassphrase']) {
                sh "ssh ${SSH_OPTS} ec2-user@${TEST_RUNNER_HOST} 'cd tower-qa && ./tools/jenkins/scripts/cleanup.sh'"
                sh 'ansible-playbook -v -i playbooks/inventory -e @playbooks/test_runner_vars.yml playbooks/reap-tower-ec2.yml'
            }
        }
    }
}
