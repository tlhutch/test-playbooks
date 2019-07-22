pipeline {

    agent none

    parameters {
        string(
            name: 'TOWER_VERSION',
            defaultValue: 'devel',
            description: 'Tower version to build'
        )
    }

    options {
        timestamps()
        buildDiscarder(logRotator(daysToKeepStr: '30'))
    }

    stages {

        stage('Build Tower Brew RPM') {
            steps {
                build(
                    job: '../Brew/Build_Tower_Brew_RPM',
                    parameters: [
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${params.TOWER_VERSION}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('Build Tower Brew Container Images') {
            steps {
                build(
                    job: '../Brew/Build_Tower_Brew_Container_Image',
                    parameters: [
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${params.TOWER_VERSION}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }

        stage('Push Brew Container Images') {
            steps {
                build(
                    job: '../Brew/Push_Brew_Container_Image',
                    parameters: [
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${params.TOWER_VERSION}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }
    }
}
