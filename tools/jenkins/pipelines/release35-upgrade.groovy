pipeline {

    agent none

    parameters {
        choice(
            name: 'ANSIBLE_VERSION',
            description: 'Ansible version to deploy within Tower install',
            choices: ['stable-2.8', 'devel', 'stable-2.9', 'stable-2.7', 'stable-2.6', 'stable-2.5',
                      'stable-2.4', 'stable-2.3']
        )
        choice(
            name: 'UPGRADE_TO',
            description: 'Tower version to upgrade to',
            choices: ['devel', '3.6.0', '3.5.4']
        )
        choice(
            name: 'PLATFORM',
            description: 'The OS to install the Tower instance on',
            choices: ['rhel-7.7-x86_64', 'rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'rhel-8.1-x86_64', 'rhel-8.0-x86_64', 'centos-7.latest-x86_64',
                      'ubuntu-16.04-x86_64', 'ubuntu-14.04-x86_64']
        )
    }

    options {
        timestamps()
        timeout(time: 10, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage('Display Information') {
            steps {
                echo "Testing Upgrade to: ${params.UPGRADE_TO}"
            }
        }

        stage('From 3.5.0') {
            parallel {
                stage('Bundle-Standalone') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-350-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Bundle-Cluster') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-350-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Standalone') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-350-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Cluster') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-350-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.5.1') {
            parallel {
                stage('Bundle-Standalone') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-351-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Bundle-Cluster') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-351-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Standalone') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-351-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Cluster') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-351-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.5.2') {
            parallel {
                stage('Bundle-Standalone') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                        build(
                            job: 'upgrade-pipeline',
                            parameters: [
                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.2'),
                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                string(name: 'SCENARIO', value: 'standalone'),
                                string(name: 'PLATFORM', value: params.PLATFORM),
                                string(name: 'BUNDLE', value: 'yes'),
                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-352-upgrade')
                            ]
                        )
                        }
                    }
                }

                stage('Bundle-Cluster') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-352-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Standalone') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-352-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Cluster') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-352-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.5.3') {
            parallel {
                stage('Bundle-Standalone') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-353-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Bundle-Cluster') {
                    when {
                        expression {
                            return ! params.PLATFORM.contains('ubuntu');
                        }
                    }

                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-353-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Standalone') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-353-upgrade')
                                ]
                            )
                        }
                    }
                }

                stage('Plain-Cluster') {
                    steps {
                        retry(2) {
                            build(
                                job: 'upgrade-pipeline',
                                parameters: [
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.5.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-353-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

    }
}
