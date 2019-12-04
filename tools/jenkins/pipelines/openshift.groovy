pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to test',
            choices: ['devel', '3.6.2', '3.5.4', '3.4.6', '3.3.8']
        )
        choice(
            name: 'TRIGGER_BREW_PIPELINE',
            description: 'Should the brew pipeline be run as part of this pipeline ?',
            choices: ['no', 'yes']
        )
    }

    options {
        timestamps()
        timeout(time: 18, unit: 'HOURS')
        buildDiscarder(logRotator(daysToKeepStr: '10'))
    }

    stages {

        stage ('Build Information') {
            steps {
                echo "Tower version under test: ${params.TOWER_VERSION}"

                script {
                    branch_name = params.TOWER_VERSION == 'devel' ? 'devel' : "release_${params.TOWER_VERSION}"
                    // NOTE: there are no images for the devel dependencies, so use the latest release.
                    // Update this after every release
                    upgrade_registry_namespace = 'ansible-tower-36'
                    install_registry_namespace = upgrade_registry_namespace

                    if (params.TOWER_VERSION == 'devel') {
                        prev_maj_version = '3.6.1'
                    } else if (params.TOWER_VERSION ==~ /3.6.[0-9]*/) {
                        prev_maj_version = '3.5.3'
                        prev_min_version = '3.6.1'
                        install_registry_namespace = 'ansible-tower-36'
                        upgrade_registry_namespace = 'ansible-tower-35'
                    } else if (params.TOWER_VERSION ==~ /3.5.[0-9]*/) {
                        prev_maj_version = '3.4.5'
                        prev_min_version = '3.5.3'
                        install_registry_namespace = 'ansible-tower-34'
                    } else if (params.TOWER_VERSION ==~ /3.4.[0-9]*/) {
                        prev_maj_version = '3.3.7'
                        prev_min_version = '3.4.5'
                        install_registry_namespace = 'ansible-tower-33'
                        upgrade_registry_namespace = 'ansible-tower-34'
                    } else {
                        prev_maj_version = '3.2.8'
                        prev_min_version = '3.3.7'
                        upgrade_registry_namespace = 'ansible-tower-33'
                    }
                }
            }
        }

        stage('Build Tower OpenShift TAR') {
            steps {
                build(
                    job: 'Build_Tower_OpenShift_TAR',
                    parameters: [
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${branch_name}"),
                    ]
                )
            }
        }

        stage('Trigger Brew Pipeline') {
            when {
                expression {
                    return params.TRIGGER_BREW_PIPELINE == 'yes'
                }
            }

            steps {
                build(
                    job: 'brew-pipeline',
                    parameters: [
                        string(name: 'TOWER_BRANCH', value: branch_name),
                        string(name: 'TOWER_PACKAGING_BRANCH', value: branch_name),
                    ]
                )
            }
        }


        stage('OpenShift Upgrade') {
            steps {
                script {
                    if (params.TOWER_VERSION != 'devel' && !(params.TOWER_VERSION ==~ /[0-9]*.[0-9]*.0/) ) {
                        stage('OpenShift Minor Upgrade') {
                            retry(2) {
                                build(
                                    job: 'Pipelines/openshift-upgrade-pipeline',
                                    parameters: [
                                        string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_min_version),
                                        string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION)
                                    ]
                                )
                            }
                        }
                    }
                }
                script {
                    if (!(params.TOWER_VERSION ==~ /3.3.[0-9]*/)) {
                        stage('OpenShift Major Upgrade') {
                            retry(2) {
                                build(
                                    job: 'Pipelines/openshift-upgrade-pipeline',
                                    parameters: [
                                        string(name: 'TOWER_VERSION_TO_UPGRADE_FROM', value: prev_maj_version),
                                        string(name: 'TOWER_VERSION_TO_UPGRADE_TO', value: params.TOWER_VERSION)
                                    ]
                                )
                            }
                        }
                    }
                }
            }
        }

        stage('OpenShift Backup and Restore') {
            steps {
                retry(2) {
                    build(
                        job: 'Pipelines/openshift-backup-and-restore-pipeline',
                        parameters: [
                            string(name: 'TOWER_VERSION', value: params.TOWER_VERSION)
                        ]
                    )
                }
            }
        }

        stage('OpenShift Install and Integration') {
            steps {
                build(
                    job: 'Pipelines/openshift-integration-pipeline',
                    parameters: [
                        string(name: 'TOWER_VERSION', value: params.TOWER_VERSION)
                    ]
                )
            }
        }

    }

    post {
        always {
            node('jenkins-jnlp-agent') {
                script {
                    json = "{\"os\":\"OpenShift\", \"tower\": \"${params.TOWER_VERSION}\", \"status\": \"${currentBuild.result}\", \"url\": \"${env.RUN_DISPLAY_URL}\"}"
                }
                sh "curl -v -X POST 'http://tower-qe-dashboard.ansible.eng.rdu2.redhat.com/jenkins/results' -H 'Content-type: application/json' -d '${json}'"
            }
        }
    }
}
