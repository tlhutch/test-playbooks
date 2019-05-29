pipeline {

    agent { label 'jenkins-jnlp-agent' }

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to test',
            choices: ['devel', '3.5.0', '3.4.4', '3.3.6']
        )
        choice(
            name: 'ANSIBLE_VERSION',
            description: 'Ansible version to deploy within Tower install',
            choices: ['devel', 'stable-2.8', 'stable-2.7', 'stable-2.6', 'stable-2.5',
                      'stable-2.4', 'stable-2.3']
        )
        choice(
            name: 'PLATFORM',
            description: 'The OS to install the Tower instance on',
            choices: ['rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'rhel-8.0-x86_64', 'ol-7.6-x86_64', 'centos-7.latest-x86_64',
                      'ubuntu-16.04-x86_64', 'ubuntu-14.04-x86_64']
        )
    }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage ('Build Information') {
            steps {
                echo """Tower version under test: ${params.TOWER_VERSION}
Ansible version under test: ${params.ANSIBLE_VERSION}
Platform under test: ${params.PLATFORM}"""

                script {
                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.TOWER_VERSION}"
                    }

                    if (params.TOWER_VERSION == 'devel') {
                        prev_maj_version = '3.5.0'
                    } else if (params.TOWER_VERSION ==~ /3.5.[0-9]*/) {
                        prev_maj_version = '3.4.3'
                    } else if (params.TOWER_VERSION ==~ /3.4.[0-9]*/) {
                        prev_maj_version = '3.3.5'
                        prev_min_version = '3.4.3'
                    } else if (params.TOWER_VERSION ==~ /3.3.[0-9]*/) {
                        prev_maj_version = '3.2.8'
                        prev_min_version = '3.3.5'
                    } else {
                        prev_maj_version = '3.1.8'
                        prev_min_version = '3.2.7'
                    }

                    if (params.ANSIBLE_VERSION != 'stable-2.8' && params.ANSIBLE_VERSION != 'stable-2.7') {
                        testexpr = 'yolo or ansible_integration'
                    } else {
                        testexpr = ''
                    }
                }
            }
        }

        stage ('Verification') {
            parallel {
                stage ('Plain Standalone') {
                    steps {
                        script {
                            if (params.TOWER_VERSION != 'devel' && !(params.TOWER_VERSION ==~ /[0-9]*.[0-9]*.0/) ) {
                                stage('Plain-Standalone Minor Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_min_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'standalone'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'no'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-minor-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            if (!(params.PLATFORM.contains('rhel-8') && params.TOWER_VERSION ==~ /3.5.[0-9]*/)) {
                                stage('Plain-Standalone Major Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_maj_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'standalone'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'no'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-major-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            stage('Plain-Standalone Backup And Restore') {
                                retry(2) {
                                    build(
                                        job: 'backup-and-restore-pipeline',
                                        parameters: [
                                            string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                            string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                            string(name: 'SCENARIO', value: 'standalone'),
                                            string(name: 'PLATFORM', value: params.PLATFORM),
                                            string(name: 'BUNDLE', value: 'no'),
                                            string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-backup-and-restore')
                                        ]
                                    )
                                }
                            }
                        }

                        script {
                            stage('Plain-Standalone Integration') {
                                build(
                                    job: 'integration-pipeline',
                                    parameters: [
                                        string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                        string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                        string(name: 'SCENARIO', value: 'standalone'),
                                        string(name: 'PLATFORM', value: params.PLATFORM),
                                        string(name: 'BUNDLE', value: 'no'),
                                        string(name: 'TESTEXPR', value: testexpr),
                                        string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-integration')
                                    ]
                                )
                            }
                        }
                    }
                }

                stage ('Plain Cluster') {
                    steps {
                        script {
                            if (params.TOWER_VERSION != 'devel' && !(params.TOWER_VERSION ==~ /[0-9]*.[0-9]*.0/) ) {
                                stage('Plain-Cluster Minor Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_min_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'cluster'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'no'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-minor-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            if (!(params.PLATFORM.contains('rhel-8') && params.TOWER_VERSION ==~ /3.5.[0-9]*/)) {
                                stage('Plain-Cluster Major Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_maj_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'cluster'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'no'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-major-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            stage('Plain-cluster Backup And Restore') {
                                retry(2) {
                                    build(
                                        job: 'backup-and-restore-pipeline',
                                        parameters: [
                                            string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                            string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                            string(name: 'SCENARIO', value: 'cluster'),
                                            string(name: 'PLATFORM', value: params.PLATFORM),
                                            string(name: 'BUNDLE', value: 'no'),
                                            string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-backup-and-restore')
                                        ]
                                    )
                                }
                            }
                        }

                        script {
                            stage('Plain-Cluster Integration') {
                                build(
                                    job: 'integration-pipeline',
                                    parameters: [
                                        string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                        string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                        string(name: 'SCENARIO', value: 'cluster'),
                                        string(name: 'PLATFORM', value: params.PLATFORM),
                                        string(name: 'BUNDLE', value: 'no'),
                                        string(name: 'TESTEXPR', value: testexpr),
                                        string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-integration')
                                    ]
                                )
                            }
                        }
                    }
                }

                stage ('Bundle Standalone') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }
                    steps {
                        script {
                            if (params.TOWER_VERSION != 'devel' && !(params.TOWER_VERSION ==~ /[0-9]*.[0-9]*.0/) ) {
                                stage('Bundle-Standalone Minor Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_min_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'standalone'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'yes'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-minor-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            if (!(params.PLATFORM.contains('rhel-8') && params.TOWER_VERSION ==~ /3.5.[0-9]*/)) {
                                stage('Bundle-Standalone Major Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_maj_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'standalone'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'yes'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-major-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            stage('Bundle-Standalone Backup And Restore') {
                                retry(2) {
                                    build(
                                        job: 'backup-and-restore-pipeline',
                                        parameters: [
                                            string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                            string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                            string(name: 'SCENARIO', value: 'standalone'),
                                            string(name: 'PLATFORM', value: params.PLATFORM),
                                            string(name: 'BUNDLE', value: 'yes'),
                                            string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-backup-and-restore')
                                        ]
                                    )
                                }
                            }
                        }

                        script {
                            stage('Bundle-Standalone Integration') {
                                build(
                                    job: 'integration-pipeline',
                                    parameters: [
                                        string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                        string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                        string(name: 'SCENARIO', value: 'standalone'),
                                        string(name: 'PLATFORM', value: params.PLATFORM),
                                        string(name: 'BUNDLE', value: 'yes'),
                                        string(name: 'TESTEXPR', value: testexpr),
                                        string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-integration')
                                    ]
                                )
                            }
                        }
                    }
                }

                stage ('Bundle Cluster') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }
                    steps {
                        script {
                            if (params.TOWER_VERSION != 'devel' && !(params.TOWER_VERSION ==~ /[0-9]*.[0-9]*.0/) ) {
                                stage('Bundle-Cluster Minor Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_min_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'cluster'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'yes'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-minor-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            if (!(params.PLATFORM.contains('rhel-8') && params.TOWER_VERSION ==~ /3.5.[0-9]*/)) {
                                stage('Bundle-Cluster Major Upgrade') {
                                    retry(2) {
                                        build(
                                            job: 'upgrade-pipeline',
                                            propagate: false,
                                            parameters: [
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_maj_version),
                                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION),
                                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                                string(name: 'SCENARIO', value: 'cluster'),
                                                string(name: 'PLATFORM', value: params.PLATFORM),
                                                string(name: 'BUNDLE', value: 'yes'),
                                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-major-upgrade')
                                            ]
                                        )
                                    }
                                }
                            }
                        }

                        script {
                            stage('Bundle-Cluster Backup And Restore') {
                                retry(2) {
                                    build(
                                        job: 'backup-and-restore-pipeline',
                                        parameters: [
                                            string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                            string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                            string(name: 'SCENARIO', value: 'cluster'),
                                            string(name: 'PLATFORM', value: params.PLATFORM),
                                            string(name: 'BUNDLE', value: 'yes'),
                                            string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-backup-and-restore')
                                        ]
                                    )
                                }
                            }
                        }

                        script {
                            stage('Bundle-Cluster Integration') {
                                build(
                                    job: 'integration-pipeline',
                                    parameters: [
                                        string(name: 'TOWER_VERSION', value: params.TOWER_VERSION),
                                        string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                        string(name: 'SCENARIO', value: 'cluster'),
                                        string(name: 'PLATFORM', value: params.PLATFORM),
                                        string(name: 'BUNDLE', value: 'yes'),
                                        string(name: 'TESTEXPR', value: testexpr),
                                        string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-integration')
                                    ]
                                )
                            }
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            node('jenkins-jnlp-agent') {
                script {
                    json = "{\"os\":\"${params.PLATFORM}\", \"ansible\":\"${params.ANSIBLE_VERSION}\", \"tower\": \"${params.TOWER_VERSION}\", \"status\": \"${currentBuild.currentResult}\", \"url\": \"${env.RUN_DISPLAY_URL}\"}"
                }
                sh "curl -v -X POST 'http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/results' -H 'Content-type: application/json' -d '${json}'"
            }
        }
    }
}
