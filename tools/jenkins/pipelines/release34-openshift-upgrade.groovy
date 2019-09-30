pipeline {

    agent none

    parameters {
        choice(
            name: 'UPGRADE_TO',
            description: 'Tower version to upgrade to',
            choices: ['devel', '3.5.2']
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

                script {
                    if (params.UPGRADE_TO == 'devel') {
                        branch_name = 'devel'
                    } else {
                        branch_name = "release_${params.UPGRADE_TO}"
                    }
                }
            }
        }

        stage('From 3.4.0') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Upgrade',
                    parameters: [
                        string(name: 'INSTALL_AWX_SETUP_PATH', value: '/setup_openshift/ansible-tower-openshift-setup-3.4.0.tar.gz'),
                        string(name: 'TOWER_BRANCH', value: "origin/${branch_name}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('From 3.4.1') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Upgrade',
                    parameters: [
                        string(name: 'INSTALL_AWX_SETUP_PATH', value: '/setup_openshift/ansible-tower-openshift-setup-3.4.1.tar.gz'),
                        string(name: 'TOWER_BRANCH', value: "origin/${branch_name}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('From 3.4.2') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Upgrade',
                    parameters: [
                        string(name: 'INSTALL_AWX_SETUP_PATH', value: '/setup_openshift/ansible-tower-openshift-setup-3.4.2.tar.gz'),
                        string(name: 'TOWER_BRANCH', value: "origin/${branch_name}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('From 3.4.3') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Upgrade',
                    parameters: [
                        string(name: 'INSTALL_AWX_SETUP_PATH', value: '/setup_openshift/ansible-tower-openshift-setup-3.4.3.tar.gz'),
                        string(name: 'TOWER_BRANCH', value: "origin/${branch_name}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('From 3.4.4') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Upgrade',
                    parameters: [
                        string(name: 'INSTALL_AWX_SETUP_PATH', value: '/setup_openshift/ansible-tower-openshift-setup-3.4.4.tar.gz'),
                        string(name: 'TOWER_BRANCH', value: "origin/${branch_name}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }
    }
}
