pipeline {

    agent none

    parameters {
        choice(
            name: 'TOWER_VERSION',
            description: 'Tower version to test',
            choices: ['devel', '3.5.2', '3.4.5', '3.3.7']
        )
        choice(
            name: 'TRIGGER_BREW_PIPELINE',
            description: 'Should the brew pipeline be run as part of this pipeline ?',
            choices: ['no', 'yes']
        )
    }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage ('Build Information') {
            steps {
                echo "Tower version under test: ${params.TOWER_VERSION}"

                script {
                    if (params.TOWER_VERSION == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.TOWER_VERSION}"
                    }

                    upgrade_registry_namespace = 'ansible-tower-35'
                    install_registry_namespace = upgrade_registry_namespace

                    if (params.TOWER_VERSION == 'devel') {
                        prev_maj_version = '3.5.1'
                    } else if (params.TOWER_VERSION ==~ /3.5.[0-9]*/) {
                        prev_maj_version = '3.4.4'
                        prev_min_version = '3.5.1'
                        install_registry_namespace = 'ansible-tower-34'
                    } else if (params.TOWER_VERSION ==~ /3.4.[0-9]*/) {
                        prev_maj_version = '3.3.6'
                        prev_min_version = '3.4.4'
                        install_registry_namespace = 'ansible-tower-33'
                        upgrade_registry_namespace = 'ansible-tower-34'
                    } else {
                        prev_maj_version = '3.2.8'
                        prev_min_version = '3.3.6'
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
                        string(name: 'TOWER_PACKAGING_BRANCH', value: branch_name)
                    ]
                )
            }
        }


        stage('OpenShift Upgrade') {
            steps {
                script {
                    if (params.TOWER_VERSION != 'devel' && !(params.TOWER_VERSION ==~ /[0-9]*.[0-9]*.0/) ) {
                        stage('OpenShift Minor Upgrade') {
                            build(
                                job: 'Test_Tower_OpenShift_Upgrade',
                                parameters: [
                                    string(name: 'TOWER_BRANCH', value: "origin/${branch_name}"),
                                    string(name: 'INSTALL_AWX_SETUP_PATH', value: "/setup_openshift/ansible-tower-openshift-setup-${prev_min_version}.tar.gz"),
                                    string(name: 'INSTALL_REGISTRY_NAMESPACE', value: upgrade_registry_namespace),
                                    string(name: 'UPGRADE_REGISTRY_NAMESPACE', value: upgrade_registry_namespace),
                                    booleanParam(name: 'TRIGGER', value: false)
                                ]
                            )
                        }
                    }
                }
                script {
                    if (!(params.TOWER_VERSION ==~ /3.3.[0-9]*/)) {
                        stage('OpenShift Major Upgrade') {
                           build(
                               job: 'Test_Tower_OpenShift_Upgrade',
                               parameters: [
                                   string(name: 'TOWER_BRANCH', value: "origin/${branch_name}"),
                                   string(name: 'INSTALL_AWX_SETUP_PATH', value: "/setup_openshift/ansible-tower-openshift-setup-${prev_maj_version}.tar.gz"),
                                   string(name: 'INSTALL_REGISTRY_NAMESPACE', value: install_registry_namespace),
                                   string(name: 'UPGRADE_REGISTRY_NAMESPACE', value: upgrade_registry_namespace),
                                   booleanParam(name: 'TRIGGER', value: false)
                               ]
                           )
                        }
                    }
                }
            }
        }

        stage('OpenShift Backup and Restore') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Backup_And_Restore',
                    parameters: [
                        string(name: 'GIT_BRANCH', value: "origin/${branch_name}"),
                        string(name: 'RABBITMQ_CONTAINER_IMAGE', value: "registry.access.redhat.com/${upgrade_registry_namespace}/ansible-tower-messaging"),
                        string(name: 'MEMCACHED_CONTAINER_IMAGE', value: "registry.access.redhat.com/${upgrade_registry_namespace}/ansible-tower-memcached"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('OpenShift Deploy') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Deploy',
                    parameters: [
                        string(name: 'GIT_BRANCH', value: "origin/${branch_name}"),
                        string(name: 'RABBITMQ_CONTAINER_IMAGE', value: "registry.access.redhat.com/${upgrade_registry_namespace}/ansible-tower-messaging"),
                        string(name: 'MEMCACHED_CONTAINER_IMAGE', value: "registry.access.redhat.com/${upgrade_registry_namespace}/ansible-tower-memcached"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('OpenShift Integration') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Integration',
                    parameters: [
                        string(name: 'GIT_BRANCH', value: "origin/${branch_name}"),
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
