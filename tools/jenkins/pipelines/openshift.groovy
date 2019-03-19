pipeline {

    agent none

    parameters {
        string(
            name: 'TOWER_RELEASE',
            defaultValue: 'devel',
            description: 'Tower release to build'
        )
    }

    options {
        timestamps()
    }

    stages {

        stage('Build Tower OpenShift TAR') {
            steps {
                build(
                    job: 'Build_Tower_OpenShift_TAR',
                    parameters: [
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${params.TOWER_RELEASE}"),
                    ]
                )
            }
        }

        stage('Trigger Brew Pipeline') {
            steps {
                build(
                    job: 'brew',
                    parameters: [
                        string(name: 'TOWER_RELEASE', value: params.TOWER_RELEASE),
                    ]
                )
            }
        }

        stage('OpenShift Deploy') {
            steps {
                build(
                    job: 'Test_Tower_OpenShift_Deploy',
                    parameters: [
                        string(name: 'GIT_BRANCH', value: "origin/${params.TOWER_RELEASE}"),
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
                        string(name: 'GIT_BRANCH', value: "origin/${params.TOWER_RELEASE}"),
                    ]
                )
            }
        }

    }
}
