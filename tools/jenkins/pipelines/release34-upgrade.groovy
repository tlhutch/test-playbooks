pipeline {

    agent none

    parameters {
        choice(
            name: 'ANSIBLE_VERSION',
            description: 'Ansible version to deploy within Tower install',
            choices: ['stable-2.7', 'devel', 'stable-2.9', 'stable-2.8', 'stable-2.6', 'stable-2.5',
                      'stable-2.4', 'stable-2.3']
        )
        choice(
            name: 'UPGRADE_TO',
            description: 'Tower version to upgrade to',
            choices: ['devel', '3.6.0', '3.5.4', '3.4.6']
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
        buildDiscarder(logRotator(daysToKeepStr: '10'))
    }

    stages {

        stage('Display Information') {
            steps {
                echo "Testing Upgrade to: ${params.UPGRADE_TO}"
            }
        }

        stage('From 3.4.0') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-340-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-340-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-340-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-340-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.4.1') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-341-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-341-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-341-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-341-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.4.2') {
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
                                string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.2'),
                                string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                string(name: 'SCENARIO', value: 'standalone'),
                                string(name: 'PLATFORM', value: params.PLATFORM),
                                string(name: 'BUNDLE', value: 'yes'),
                                string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-342-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-342-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-342-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-342-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.4.3') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-343-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-343-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-343-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-343-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.4.4') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-344-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-344-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-344-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-344-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.4.5') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-345-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-345-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-345-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.4.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-345-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }
    }
}
