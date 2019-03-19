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

        stage('Build Tower Brew RPM') {
            steps {
                build(
                    job: '../Brew/Build_Tower_Brew_RPM',
                    parameters: [
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${params.TOWER_RELEASE}"),
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
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${params.TOWER_RELEASE}"),
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
                        string(name: 'TOWER_PACKAGING_BRANCH', value: "origin/${params.TOWER_RELEASE}"),
                        booleanParam(name: 'TRIGGER', value: false)
                    ]
                )
            }
        }
    }
}
