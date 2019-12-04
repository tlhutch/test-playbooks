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
            choices: ['devel', '3.5.2']
        )
        choice(
            name: 'PLATFORM',
            description: 'The OS to install the Tower instance on',
            choices: ['rhel-7.7-x86_64', 'rhel-7.6-x86_64', 'rhel-7.5-x86_64', 'rhel-7.4-x86_64',
                      'centos-7.latest-x86_64', 'ubuntu-16.04-x86_64']
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

        stage('From 3.3.0') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-330-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-330-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-330-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.0'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-330-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.3.1') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-331-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-331-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-331-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.1'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-331-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.3.2') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-332-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-332-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-332-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.2'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-332-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.3.3') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-333-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-333-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-333-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.3'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-333-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.3.4') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-334-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-334-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-334-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.4'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-334-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.3.5') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-335-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-335-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-335-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.5'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-335-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }

        stage('From 3.3.6') {
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.6'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-standalone-336-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.6'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'yes'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-bundle-cluster-336-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.6'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'standalone'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-standalone-336-upgrade')
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
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: '3.3.6'),
                                    string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.UPGRADE_TO),
                                    string(name: 'ANSIBLE_VERSION', value: params.ANSIBLE_VERSION),
                                    string(name: 'SCENARIO', value: 'cluster'),
                                    string(name: 'PLATFORM', value: params.PLATFORM),
                                    string(name: 'BUNDLE', value: 'no'),
                                    string(name: 'DEPLOYMENT_NAME', value: 'evergreen-jenkins-tower-plain-cluster-336-upgrade')
                                ]
                            )
                        }
                    }
                }
            }
        }
    }
}

